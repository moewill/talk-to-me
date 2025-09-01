"""
Audio Processor for Voice-driven Claude CLI automation system.

This module handles audio processing using OpenAI Whisper for local speech-to-text
conversion. It provides asynchronous transcription capabilities with audio format
conversion and error handling.
"""

import asyncio
import io
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("OpenAI Whisper not available. Audio processing will be limited.")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile not available. Some audio formats may not be supported.")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available. Audio format conversion will be limited.")


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""
    success: bool
    text: str
    confidence: float
    language: Optional[str]
    processing_time: float
    error: Optional[str]
    audio_duration: Optional[float]


@dataclass
class AudioStats:
    """Statistics for audio processing."""
    total_transcriptions: int
    successful_transcriptions: int
    failed_transcriptions: int
    average_processing_time: float
    average_audio_duration: float
    last_transcription: Optional[float]


class AudioProcessor:
    """
    Handles audio processing and speech-to-text conversion using Whisper.
    
    Provides asynchronous transcription capabilities with support for various
    audio formats, automatic format conversion, and comprehensive error handling.
    """
    
    def __init__(
        self,
        model_name: str = "base",
        language: Optional[str] = None,
        device: str = "auto"
    ):
        """
        Initialize the audio processor.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
            language: Target language for transcription (None for auto-detect)
            device: Device to use for processing (auto, cpu, cuda)
        """
        self.model_name = model_name
        self.language = language
        # Resolve "auto" device to specific device to avoid torch storage issues
        if device == "auto":
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.debug(f"Resolved auto device to: {self.device}")
        else:
            self.device = device
        self.model = None
        self.model_loaded = False
        
        # Audio processing parameters
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.max_audio_length = 30.0  # Maximum audio length in seconds
        
        # Statistics tracking
        self._stats = AudioStats(
            total_transcriptions=0,
            successful_transcriptions=0,
            failed_transcriptions=0,
            average_processing_time=0.0,
            average_audio_duration=0.0,
            last_transcription=None
        )
        
        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        if not WHISPER_AVAILABLE:
            logger.error("OpenAI Whisper is required but not installed")
            raise ImportError("OpenAI Whisper is required for audio processing. Install with: pip install openai-whisper")
            
        if not SOUNDFILE_AVAILABLE:
            logger.warning("soundfile not available - some audio formats may not work")
            
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available - audio format conversion limited")

    async def load_model(self) -> bool:
        """
        Load the Whisper model asynchronously.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if self.model_loaded:
            return True
            
        if not WHISPER_AVAILABLE:
            logger.error("Cannot load model: Whisper not available")
            return False
            
        try:
            # Load model directly (bypass thread executor to avoid pickle issues)
            import whisper
            import torch
            
            # Enhanced debugging information
            logger.debug(f"Starting Whisper model loading - Model: {self.model_name}, Device: {self.device}")
            logger.debug(f"PyTorch version: {torch.__version__}")
            logger.debug(f"Whisper version: {getattr(whisper, '__version__', 'unknown')}")
            logger.debug(f"CUDA available: {torch.cuda.is_available()}")
            logger.debug(f"Cache directory: {os.path.expanduser('~/.cache/whisper')}")
            
            # Patch torch.load temporarily for model loading
            original_load = torch.load
            
            def whisper_compatible_load(*args, **kwargs):
                logger.debug(f"torch.load called with args: {len(args)} kwargs: {list(kwargs.keys())}")
                kwargs['weights_only'] = False
                logger.debug("Applied weights_only=False patch")
                return original_load(*args, **kwargs)
            
            torch.load = whisper_compatible_load
            logger.debug("Applied torch.load patch")
            
            try:
                logger.debug("Calling whisper.load_model()...")
                self.model = whisper.load_model(self.model_name, device=self.device)
                self.model_loaded = True
                logger.info(f"Whisper model '{self.model_name}' loaded successfully")
                logger.debug(f"Model type: {type(self.model)}")
                return True
            finally:
                # Restore original torch.load
                torch.load = original_load
                logger.debug("Restored original torch.load")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def _load_model_sync(self):
        """Load Whisper model synchronously."""
        try:
            # Use weights_only=False to avoid the weights loading error
            # This is safe since we're loading from the official Whisper repository
            import torch
            
            # Temporarily set torch loading to allow pickle loading
            original_load = torch.load
            
            def safe_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            
            torch.load = safe_load
            
            try:
                model = whisper.load_model(self.model_name, device=self.device)
                return model
            finally:
                # Restore original torch.load
                torch.load = original_load
                
        except Exception as e:
            logger.error(f"Model loading error: {e}")
            raise

    async def transcribe(
        self, 
        audio_data: Union[bytes, np.ndarray], 
        audio_format: str = "wav"
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio data as bytes or numpy array
            audio_format: Format of the audio data (wav, mp3, etc.)
            
        Returns:
            TranscriptionResult with transcription details
        """
        start_time = time.time()
        
        try:
            # Ensure model is loaded
            if not await self.load_model():
                return TranscriptionResult(
                    success=False,
                    text="",
                    confidence=0.0,
                    language=None,
                    processing_time=0.0,
                    error="Failed to load Whisper model",
                    audio_duration=None
                )
            
            # Convert audio data to numpy array
            audio_array, duration = await self._prepare_audio(audio_data, audio_format)
            
            if audio_array is None:
                return TranscriptionResult(
                    success=False,
                    text="",
                    confidence=0.0,
                    language=None,
                    processing_time=time.time() - start_time,
                    error="Failed to process audio data",
                    audio_duration=duration
                )
            
            # Perform transcription
            result = await self._transcribe_sync(audio_array)
            
            processing_time = time.time() - start_time
            
            # Create TranscriptionResult
            transcription_result = TranscriptionResult(
                success=True,
                text=result["text"].strip(),
                confidence=self._calculate_confidence(result),
                language=result.get("language"),
                processing_time=processing_time,
                error=None,
                audio_duration=duration
            )
            
            # Update statistics
            self._update_stats(transcription_result, processing_time, duration)
            
            return transcription_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = TranscriptionResult(
                success=False,
                text="",
                confidence=0.0,
                language=None,
                processing_time=processing_time,
                error=str(e),
                audio_duration=None
            )
            
            self._update_stats(error_result, processing_time, 0.0)
            logger.error(f"Transcription error: {e}")
            return error_result

    async def _prepare_audio(
        self, 
        audio_data: Union[bytes, np.ndarray], 
        audio_format: str
    ) -> tuple[Optional[np.ndarray], Optional[float]]:
        """
        Prepare audio data for transcription.
        
        Args:
            audio_data: Raw audio data
            audio_format: Format of the audio data
            
        Returns:
            Tuple of (processed_audio_array, duration_in_seconds)
        """
        try:
            if isinstance(audio_data, np.ndarray):
                # Already a numpy array
                audio_array = audio_data
                duration = len(audio_array) / self.sample_rate
            else:
                # Convert bytes to numpy array
                audio_array, duration = await self._bytes_to_numpy(audio_data, audio_format)
            
            if audio_array is None:
                return None, None
            
            # Ensure correct sample rate
            if hasattr(self, '_last_sample_rate') and self._last_sample_rate != self.sample_rate:
                audio_array = await self._resample_audio(audio_array, self._last_sample_rate)
            
            # Normalize audio
            audio_array = audio_array.astype(np.float32)
            
            # Ensure audio is not too long
            if duration > self.max_audio_length:
                logger.warning(f"Audio duration {duration:.1f}s exceeds maximum {self.max_audio_length}s")
                # Truncate to maximum length
                max_samples = int(self.max_audio_length * self.sample_rate)
                audio_array = audio_array[:max_samples]
                duration = self.max_audio_length
            
            return audio_array, duration
            
        except Exception as e:
            logger.error(f"Error preparing audio: {e}")
            return None, None

    async def _bytes_to_numpy(
        self, 
        audio_bytes: bytes, 
        audio_format: str
    ) -> tuple[Optional[np.ndarray], Optional[float]]:
        """
        Convert audio bytes to numpy array.
        
        Args:
            audio_bytes: Raw audio data as bytes
            audio_format: Format of the audio data
            
        Returns:
            Tuple of (numpy_array, duration_in_seconds)
        """
        try:
            # Handle raw PCM data directly (from browser WebAudio)
            if audio_format == "raw_pcm":
                # Convert raw PCM bytes to numpy array (assume 16-bit signed integers)
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                duration = len(audio_array) / self.sample_rate
                self._last_sample_rate = self.sample_rate
                
                # Enhanced debugging for audio characteristics
                logger.debug(f"Raw PCM audio debug:")
                logger.debug(f"  - Bytes received: {len(audio_bytes)}")
                logger.debug(f"  - Samples count: {len(audio_array)}")
                logger.debug(f"  - Duration: {duration:.3f}s")
                logger.debug(f"  - Sample rate assumed: {self.sample_rate} Hz")
                logger.debug(f"  - Audio RMS level: {np.sqrt(np.mean(audio_array**2)):.6f}")
                logger.debug(f"  - Audio peak level: {np.max(np.abs(audio_array)):.6f}")
                logger.debug(f"  - Non-zero samples: {np.count_nonzero(audio_array)}/{len(audio_array)}")
                
                # Check if audio is essentially silent
                rms_level = np.sqrt(np.mean(audio_array**2))
                if rms_level < 0.001:
                    logger.warning(f"Audio appears to be silent (RMS: {rms_level:.6f})")
                elif rms_level < 0.01:
                    logger.warning(f"Audio appears to be very quiet (RMS: {rms_level:.6f}) - consider speaking louder or adjusting microphone")
                    
                # Warn about potential sample rate mismatch
                expected_samples_16k = len(audio_bytes) / 2  # 16-bit = 2 bytes per sample
                if len(audio_array) != expected_samples_16k:
                    logger.warning(f"Sample count mismatch - expected {expected_samples_16k}, got {len(audio_array)}")
                    logger.warning("Browser may be sending different sample rate than 16kHz")
                
                return audio_array, duration
            
            # Create temporary file for other audio formats
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Try using soundfile first (more reliable)
                if SOUNDFILE_AVAILABLE:
                    audio_array, sample_rate = sf.read(temp_file_path)
                    self._last_sample_rate = sample_rate
                    duration = len(audio_array) / sample_rate
                    return audio_array, duration
                
                # Fallback to pydub
                elif PYDUB_AVAILABLE:
                    audio_segment = AudioSegment.from_file(temp_file_path, format=audio_format)
                    
                    # Convert to numpy array
                    audio_array = np.array(audio_segment.get_array_of_samples())
                    
                    # Handle stereo audio
                    if audio_segment.channels == 2:
                        audio_array = audio_array.reshape((-1, 2))
                        audio_array = audio_array.mean(axis=1)  # Convert to mono
                    
                    # Normalize to float32
                    audio_array = audio_array.astype(np.float32) / 32768.0
                    
                    self._last_sample_rate = audio_segment.frame_rate
                    duration = len(audio_segment) / 1000.0  # pydub uses milliseconds
                    
                    return audio_array, duration
                
                else:
                    logger.error("No audio processing library available")
                    return None, None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Error converting audio bytes to numpy: {e}")
            return None, None

    async def _resample_audio(self, audio_array: np.ndarray, original_rate: int) -> np.ndarray:
        """
        Resample audio to target sample rate.
        
        Args:
            audio_array: Audio data as numpy array
            original_rate: Original sample rate
            
        Returns:
            Resampled audio array
        """
        try:
            if original_rate == self.sample_rate:
                return audio_array
            
            # Simple resampling (for production, consider using librosa)
            ratio = self.sample_rate / original_rate
            new_length = int(len(audio_array) * ratio)
            
            # Linear interpolation resampling
            old_indices = np.linspace(0, len(audio_array) - 1, new_length)
            resampled = np.interp(old_indices, np.arange(len(audio_array)), audio_array)
            
            return resampled.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error resampling audio: {e}")
            return audio_array

    async def _transcribe_sync(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """
        Perform synchronous transcription using Whisper.
        
        Args:
            audio_array: Prepared audio data
            
        Returns:
            Whisper transcription result
        """
        loop = asyncio.get_event_loop()
        
        # Run transcription in thread to avoid blocking
        result = await loop.run_in_executor(
            None,
            self._run_whisper_transcription,
            audio_array
        )
        
        return result

    def _run_whisper_transcription(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Run Whisper transcription synchronously."""
        options = {}
        if self.language:
            options["language"] = self.language
            
        return self.model.transcribe(audio_array, **options)

    def _calculate_confidence(self, whisper_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score from Whisper result.
        
        Args:
            whisper_result: Result from Whisper transcription
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Whisper doesn't provide direct confidence scores
        # We'll estimate based on available information
        
        text = whisper_result.get("text", "").strip()
        
        if not text:
            return 0.0
        
        # Basic confidence estimation
        confidence = 0.7  # Base confidence
        
        # Bonus for longer text (more context)
        if len(text) > 10:
            confidence += 0.1
        
        # Bonus for detected language
        if whisper_result.get("language"):
            confidence += 0.1
        
        # Check for common transcription artifacts that suggest lower confidence
        artifacts = ["[BLANK_AUDIO]", "[inaudible]", "...", "???"]
        for artifact in artifacts:
            if artifact.lower() in text.lower():
                confidence -= 0.3
                break
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    def _update_stats(
        self, 
        result: TranscriptionResult, 
        processing_time: float, 
        audio_duration: float
    ) -> None:
        """Update processing statistics."""
        self._stats.total_transcriptions += 1
        
        if result.success:
            self._stats.successful_transcriptions += 1
        else:
            self._stats.failed_transcriptions += 1
        
        # Update average processing time
        if self._stats.total_transcriptions == 1:
            self._stats.average_processing_time = processing_time
            self._stats.average_audio_duration = audio_duration
        else:
            # Running averages
            total = self._stats.total_transcriptions
            self._stats.average_processing_time = (
                (self._stats.average_processing_time * (total - 1) + processing_time) / total
            )
            self._stats.average_audio_duration = (
                (self._stats.average_audio_duration * (total - 1) + audio_duration) / total
            )
        
        self._stats.last_transcription = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats_dict = {
            'total_transcriptions': self._stats.total_transcriptions,
            'successful_transcriptions': self._stats.successful_transcriptions,
            'failed_transcriptions': self._stats.failed_transcriptions,
            'average_processing_time': self._stats.average_processing_time,
            'average_audio_duration': self._stats.average_audio_duration,
            'last_transcription': self._stats.last_transcription,
            'model_name': self.model_name,
            'model_loaded': self.model_loaded,
            'language': self.language,
            'device': self.device
        }
        
        # Add success rate
        if self._stats.total_transcriptions > 0:
            stats_dict['success_rate'] = (
                self._stats.successful_transcriptions / self._stats.total_transcriptions
            )
        else:
            stats_dict['success_rate'] = 0.0
        
        return stats_dict

    async def test_transcription(self) -> Dict[str, Any]:
        """
        Test transcription functionality with a simple audio sample.
        
        Returns:
            Test results dictionary
        """
        try:
            # Generate a simple test audio (1 second of silence)
            test_audio = np.zeros(self.sample_rate, dtype=np.float32)
            
            result = await self.transcribe(test_audio)
            
            return {
                'model_available': WHISPER_AVAILABLE,
                'model_loaded': self.model_loaded,
                'test_successful': result.success,
                'processing_time': result.processing_time,
                'error': result.error
            }
            
        except Exception as e:
            return {
                'model_available': WHISPER_AVAILABLE,
                'model_loaded': self.model_loaded,
                'test_successful': False,
                'processing_time': 0.0,
                'error': str(e)
            }

    def clear_model(self) -> None:
        """Clear the loaded model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self.model_loaded = False
            logger.info("Whisper model cleared from memory")


# Example usage and testing
if __name__ == "__main__":
    async def test_audio_processor():
        """Test the audio processor functionality."""
        processor = AudioProcessor(model_name="base")
        
        print("Testing Audio Processor...")
        print("=" * 40)
        
        # Test model loading
        print("Loading Whisper model...")
        model_loaded = await processor.load_model()
        print(f"Model loaded: {model_loaded}")
        print()
        
        if not model_loaded:
            print("Cannot proceed without model. Ending test.")
            return
        
        # Test with simple audio
        test_result = await processor.test_transcription()
        print(f"Transcription Test: {test_result}")
        print()
        
        # Generate test audio (simple sine wave)
        duration = 2.0  # seconds
        sample_rate = 16000
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        test_audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.1
        
        print("Testing with generated audio...")
        result = await processor.transcribe(test_audio)
        
        print(f"Success: {result.success}")
        print(f"Text: '{result.text}'")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        print(f"Audio Duration: {result.audio_duration:.2f}s")
        
        if not result.success:
            print(f"Error: {result.error}")
        
        print("-" * 40)
        
        # Print statistics
        stats = processor.get_stats()
        print(f"Statistics: {stats}")
    
    # Run the test
    asyncio.run(test_audio_processor())
