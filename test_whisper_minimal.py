#!/usr/bin/env python3
"""
Minimal Whisper Test Script
Validates that Whisper model loading and basic transcription works in the fixed environment.
"""

import sys
import time
import numpy as np

def test_whisper_basic():
    """Test basic Whisper functionality."""
    print("🎤 Testing Whisper Model Loading and Basic Transcription")
    print("=" * 60)
    
    try:
        # Test import
        print("1. Testing Whisper import...")
        import whisper
        print("   ✓ Whisper imported successfully")
        
        # Test model loading
        print("2. Loading Whisper 'base' model...")
        start_time = time.time()
        model = whisper.load_model("base")
        load_time = time.time() - start_time
        print(f"   ✓ Model loaded in {load_time:.2f} seconds")
        
        # Test with simple audio (silence)
        print("3. Testing transcription with generated audio...")
        
        # Generate 2 seconds of silence (16kHz sample rate)
        sample_rate = 16000
        duration = 2.0
        audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        # Transcribe
        start_time = time.time()
        result = model.transcribe(audio_data)
        transcribe_time = time.time() - start_time
        
        print(f"   ✓ Transcription completed in {transcribe_time:.2f} seconds")
        print(f"   Text: '{result['text'].strip()}'")
        print(f"   Language: {result.get('language', 'unknown')}")
        
        # Test with simple tone (A4 note)
        print("4. Testing with generated sine wave...")
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        sine_wave = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.1
        
        start_time = time.time()
        result = model.transcribe(sine_wave)
        transcribe_time = time.time() - start_time
        
        print(f"   ✓ Sine wave transcription completed in {transcribe_time:.2f} seconds")
        print(f"   Text: '{result['text'].strip()}'")
        
        print("\n" + "=" * 60)
        print("🎉 ALL WHISPER TESTS PASSED!")
        print("   • Model loading: WORKING")
        print("   • Transcription: WORKING") 
        print("   • Audio processing: WORKING")
        print("   • System is ready for voice processing!")
        return True
        
    except Exception as e:
        print(f"\n❌ WHISPER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_formats():
    """Test different audio format handling capabilities."""
    print("\n🎵 Testing Audio Format Support")
    print("-" * 40)
    
    try:
        # Test soundfile
        print("1. Testing soundfile...")
        import soundfile as sf
        print(f"   ✓ soundfile version: {getattr(sf, '__version__', 'unknown')}")
        
        # Test pydub
        print("2. Testing pydub...")
        from pydub import AudioSegment
        print("   ✓ pydub imported successfully")
        
        # Test basic numpy audio processing
        print("3. Testing numpy audio processing...")
        sample_rate = 16000
        duration = 1.0
        test_audio = np.random.random(int(sample_rate * duration)).astype(np.float32) * 0.1
        print(f"   ✓ Generated test audio: {len(test_audio)} samples")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Audio format test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting minimal Whisper validation test...")
    print()
    
    whisper_success = test_whisper_basic()
    audio_success = test_audio_formats()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print("=" * 60)
    
    if whisper_success and audio_success:
        print("🎉 ALL TESTS PASSED!")
        print("   AudioProcessor foundation is ready for integration!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Fix the issues above before proceeding.")
        sys.exit(1)