#!/usr/bin/env python3
"""
Test the current AudioProcessor implementation to reproduce the exact error.
"""

import sys
import traceback
sys.path.append('src')

def test_audio_processor_import():
    """Test importing AudioProcessor."""
    print("Testing AudioProcessor import...")
    try:
        from audio_processor import AudioProcessor
        print("✓ AudioProcessor imported successfully")
        return True, AudioProcessor
    except Exception as e:
        print(f"✗ AudioProcessor import failed: {e}")
        traceback.print_exc()
        return False, None

def test_audio_processor_init():
    """Test AudioProcessor initialization."""
    print("\nTesting AudioProcessor initialization...")
    try:
        from audio_processor import AudioProcessor
        processor = AudioProcessor(model_name="base", device="cpu")
        print("✓ AudioProcessor initialized successfully")
        return True, processor
    except Exception as e:
        print(f"✗ AudioProcessor initialization failed: {e}")
        traceback.print_exc()
        return False, None

def test_model_loading():
    """Test the actual model loading that's failing."""
    print("\nTesting AudioProcessor.load_model()...")
    try:
        from audio_processor import AudioProcessor
        processor = AudioProcessor(model_name="base", device="cpu")
        
        print("Attempting to load model...")
        import asyncio
        
        async def test_load():
            result = await processor.load_model()
            return result
            
        result = asyncio.run(test_load())
        
        if result:
            print("✓ Model loading successful")
            return True
        else:
            print("✗ Model loading failed (returned False)")
            return False
            
    except Exception as e:
        print(f"✗ Model loading failed with exception: {e}")
        traceback.print_exc()
        return False

def test_transcription():
    """Test transcription with sample audio."""
    print("\nTesting transcription...")
    try:
        from audio_processor import AudioProcessor
        import numpy as np
        import asyncio
        
        processor = AudioProcessor(model_name="base", device="cpu")
        
        async def test_transcribe():
            # Load model first
            if not await processor.load_model():
                print("✗ Could not load model for transcription test")
                return False
            
            # Generate test audio (2 seconds of silence)
            sample_rate = 16000
            duration = 2
            audio_data = np.zeros(sample_rate * duration, dtype=np.float32)
            
            result = await processor.transcribe(audio_data)
            print(f"Transcription result: {result}")
            return result.success
            
        result = asyncio.run(test_transcribe())
        
        if result:
            print("✓ Transcription test successful")
            return True
        else:
            print("✗ Transcription test failed")
            return False
            
    except Exception as e:
        print(f"✗ Transcription test failed with exception: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests to reproduce the error."""
    print("=== Current AudioProcessor Test ===\n")
    
    results = []
    
    # Test 1: Import
    success, processor_class = test_audio_processor_import()
    results.append(success)
    if not success:
        print("\n❌ Cannot proceed - import failed")
        return
    
    # Test 2: Initialize
    success, processor = test_audio_processor_init()
    results.append(success)
    if not success:
        print("\n❌ Cannot proceed - initialization failed")
        return
    
    # Test 3: Model Loading (this should reproduce the error)
    success = test_model_loading()
    results.append(success)
    
    # Test 4: Transcription (if model loading worked)
    if success:
        transcription_success = test_transcription()
        results.append(transcription_success)
    else:
        print("\n⚠️  Skipping transcription test - model loading failed")
        results.append(False)
    
    print(f"\n=== Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All tests passed - AudioProcessor is working!")
    else:
        print("❌ Some tests failed - this should help identify the issue")

if __name__ == "__main__":
    main()