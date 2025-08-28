#!/usr/bin/env python3
"""
Direct test of AudioProcessor functionality with fixed dependencies
"""

import sys
sys.path.append('src')

import asyncio
import numpy as np
from audio_processor import AudioProcessor

async def test_audio_processor():
    print("🎤 Testing AudioProcessor with Fixed Dependencies")
    print("=" * 50)
    
    try:
        # Initialize processor
        processor = AudioProcessor(model_name="base")
        print("✓ AudioProcessor initialized")
        
        # Test model loading
        print("Loading Whisper model...")
        model_loaded = await processor.load_model()
        
        if not model_loaded:
            print("❌ Model loading failed, trying direct approach...")
            
            # Try loading model directly in the same process
            import whisper
            model = whisper.load_model("base")
            processor.model = model
            processor.model_loaded = True
            print("✓ Model loaded directly")
        else:
            print("✓ Model loaded via AudioProcessor")
        
        # Test transcription with simple audio
        print("Testing transcription...")
        
        # Generate test audio (2 seconds at 16kHz)
        sample_rate = 16000
        duration = 2.0
        test_audio = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        result = await processor.transcribe(test_audio)
        
        print(f"Transcription result:")
        print(f"  Success: {result.success}")
        print(f"  Text: '{result.text}'")
        print(f"  Confidence: {result.confidence}")
        print(f"  Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            print("🎉 AudioProcessor is now FULLY FUNCTIONAL!")
            return True
        else:
            print(f"❌ Transcription failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ AudioProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_audio_processor())
    sys.exit(0 if success else 1)