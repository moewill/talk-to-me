"""
Comprehensive tests for the AudioProcessor module.
"""

import asyncio
import io
import wave
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest
from src.audio_processor import AudioProcessor, TranscriptionResult


@pytest.fixture
def audio_processor():
    """Create an AudioProcessor instance for testing."""
    return AudioProcessor(model_name="tiny")


@pytest.fixture
def sample_audio_data():
    """Create sample audio data for testing."""
    # Generate 1 second of 16kHz sine wave (440Hz tone)
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_samples = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_samples = (audio_samples * 32767).astype(np.int16)
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_samples.tobytes())
    
    return wav_buffer.getvalue()


class TestAudioProcessor:
    """Test cases for AudioProcessor functionality."""
    
    def test_initialization(self, audio_processor):
        """Test AudioProcessor initialization."""
        assert audio_processor.model_name == "tiny"
        assert audio_processor.model is None
        assert not audio_processor.model_loaded
        assert audio_processor.stats.total_processed == 0
    
    @pytest.mark.asyncio
    async def test_load_model_success(self, audio_processor):
        """Test successful model loading."""
        with patch('whisper.load_model') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model
            
            result = await audio_processor.load_model()
            
            assert result is True
            assert audio_processor.model is mock_model
            assert audio_processor.model_loaded is True
            mock_load.assert_called_once_with("tiny")
    
    @pytest.mark.asyncio
    async def test_load_model_failure(self, audio_processor):
        """Test model loading failure."""
        with patch('whisper.load_model') as mock_load:
            mock_load.side_effect = Exception("Model load failed")
            
            result = await audio_processor.load_model()
            
            assert result is False
            assert audio_processor.model is None
            assert audio_processor.model_loaded is False
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, audio_processor, sample_audio_data):
        """Test successful audio transcription."""
        # Mock the model and its transcribe method
        mock_model = Mock()
        mock_result = {
            'text': 'Hello world',
            'language': 'en',
            'segments': [{'start': 0, 'end': 1, 'text': 'Hello world'}]
        }
        mock_model.transcribe.return_value = mock_result
        
        # Setup audio processor with mocked model
        audio_processor.model = mock_model
        audio_processor.model_loaded = True
        
        with patch('io.BytesIO'), \
             patch('soundfile.read') as mock_sf_read, \
             patch('librosa.resample') as mock_resample:
            
            # Mock soundfile.read to return audio data
            mock_sf_read.return_value = (np.array([0.1, 0.2, 0.3]), 16000)
            mock_resample.return_value = np.array([0.1, 0.2, 0.3])
            
            result = await audio_processor.transcribe(sample_audio_data)
            
            assert isinstance(result, TranscriptionResult)
            assert result.success is True
            assert result.text == 'Hello world'
            assert result.language == 'en'
            assert result.confidence > 0
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_transcribe_model_not_loaded(self, audio_processor, sample_audio_data):
        """Test transcription when model is not loaded."""
        result = await audio_processor.transcribe(sample_audio_data)
        
        assert isinstance(result, TranscriptionResult)
        assert result.success is False
        assert "Model not loaded" in result.error
        assert result.text == ""
    
    @pytest.mark.asyncio
    async def test_transcribe_invalid_audio_data(self, audio_processor):
        """Test transcription with invalid audio data."""
        audio_processor.model = Mock()
        audio_processor.model_loaded = True
        
        with patch('io.BytesIO'), \
             patch('soundfile.read') as mock_sf_read:
            
            mock_sf_read.side_effect = Exception("Invalid audio format")
            
            result = await audio_processor.transcribe(b"invalid_audio_data")
            
            assert isinstance(result, TranscriptionResult)
            assert result.success is False
            assert "Invalid audio format" in result.error
    
    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, audio_processor):
        """Test transcription with empty audio data."""
        result = await audio_processor.transcribe(b"")
        
        assert isinstance(result, TranscriptionResult)
        assert result.success is False
        assert "Empty audio data" in result.error
    
    def test_convert_audio_format_wav(self, audio_processor, sample_audio_data):
        """Test WAV audio format conversion."""
        with patch('soundfile.read') as mock_sf_read:
            mock_sf_read.return_value = (np.array([0.1, 0.2, 0.3]), 16000)
            
            result = audio_processor._convert_audio_format(sample_audio_data, "wav")
            
            assert result is not None
            assert len(result) == 3
    
    def test_convert_audio_format_unsupported(self, audio_processor):
        """Test unsupported audio format conversion."""
        result = audio_processor._convert_audio_format(b"data", "unsupported")
        
        assert result is None
    
    def test_estimate_confidence_high_quality(self, audio_processor):
        """Test confidence estimation for high-quality transcription."""
        mock_result = {
            'segments': [
                {'start': 0, 'end': 1, 'text': 'Clear speech'},
                {'start': 1, 'end': 2, 'text': 'with good quality'}
            ]
        }
        
        confidence = audio_processor._estimate_confidence(mock_result, 2.0)
        
        assert 0.0 <= confidence <= 1.0
        # Should be relatively high for clear segments
        assert confidence > 0.5
    
    def test_estimate_confidence_poor_quality(self, audio_processor):
        """Test confidence estimation for poor-quality transcription."""
        mock_result = {
            'segments': [
                {'start': 0, 'end': 10, 'text': 'uh um er'},  # Long duration, few words
                {'start': 10, 'end': 11, 'text': ''}  # Empty segment
            ]
        }
        
        confidence = audio_processor._estimate_confidence(mock_result, 11.0)
        
        assert 0.0 <= confidence <= 1.0
        # Should be lower for poor quality
        assert confidence < 0.7
    
    def test_resample_audio(self, audio_processor):
        """Test audio resampling functionality."""
        # Create test audio at 44.1kHz
        original_sr = 44100
        target_sr = 16000
        audio_data = np.random.random(44100)  # 1 second of random audio
        
        with patch('librosa.resample') as mock_resample:
            mock_resample.return_value = np.random.random(16000)
            
            result = audio_processor._resample_audio(audio_data, original_sr, target_sr)
            
            mock_resample.assert_called_once_with(audio_data, orig_sr=original_sr, target_sr=target_sr)
            assert result is not None
    
    def test_normalize_audio(self, audio_processor):
        """Test audio normalization."""
        # Create test audio with varying amplitudes
        audio_data = np.array([0.1, 0.8, -0.6, 0.3, -0.9])
        
        normalized = audio_processor._normalize_audio(audio_data)
        
        # Check that peak amplitude is around 0.9 (90% of max)
        assert np.max(np.abs(normalized)) <= 1.0
        assert np.max(np.abs(normalized)) >= 0.8  # Should be reasonably normalized
    
    def test_limit_duration(self, audio_processor):
        """Test audio duration limiting."""
        # Create 10 seconds of audio at 16kHz
        sample_rate = 16000
        max_duration = 5.0  # 5 seconds
        audio_data = np.random.random(10 * sample_rate)  # 10 seconds
        
        limited = audio_processor._limit_duration(audio_data, sample_rate, max_duration)
        
        expected_samples = int(max_duration * sample_rate)
        assert len(limited) == expected_samples
    
    def test_get_stats(self, audio_processor):
        """Test statistics retrieval."""
        # Manually update some stats
        audio_processor.stats.total_processed = 5
        audio_processor.stats.successful_transcriptions = 4
        audio_processor.stats.failed_transcriptions = 1
        
        stats = audio_processor.get_stats()
        
        assert stats['total_processed'] == 5
        assert stats['successful_transcriptions'] == 4
        assert stats['failed_transcriptions'] == 1
        assert 'success_rate' in stats
        assert 'average_processing_time' in stats
    
    @pytest.mark.asyncio
    async def test_transcribe_updates_stats(self, audio_processor, sample_audio_data):
        """Test that transcription updates statistics."""
        mock_model = Mock()
        mock_result = {
            'text': 'Test transcription',
            'language': 'en',
            'segments': [{'start': 0, 'end': 1, 'text': 'Test transcription'}]
        }
        mock_model.transcribe.return_value = mock_result
        
        audio_processor.model = mock_model
        audio_processor.model_loaded = True
        
        initial_count = audio_processor.stats.total_processed
        
        with patch('io.BytesIO'), \
             patch('soundfile.read') as mock_sf_read, \
             patch('librosa.resample') as mock_resample:
            
            mock_sf_read.return_value = (np.array([0.1, 0.2, 0.3]), 16000)
            mock_resample.return_value = np.array([0.1, 0.2, 0.3])
            
            await audio_processor.transcribe(sample_audio_data)
            
            assert audio_processor.stats.total_processed == initial_count + 1
            assert audio_processor.stats.successful_transcriptions == 1
