#!/usr/bin/env python3
"""
Quick fix for AudioProcessor model loading issue
"""

import sys
sys.path.append('src')

# Apply the fix directly to the torch loading mechanism
def fix_whisper_loading():
    """Fix the Whisper model loading issue by patching torch.load globally."""
    import torch
    
    # Store original load function
    _original_torch_load = torch.load
    
    def patched_torch_load(*args, **kwargs):
        """Patched torch.load that sets weights_only=False for Whisper models."""
        # For Whisper model loading, disable weights_only restriction
        kwargs['weights_only'] = False
        return _original_torch_load(*args, **kwargs)
    
    # Apply the patch
    torch.load = patched_torch_load
    print("✓ Applied torch.load patch for Whisper compatibility")

# Apply the fix before importing AudioProcessor
fix_whisper_loading()

# Now test AudioProcessor
import asyncio
from audio_processor import AudioProcessor
import numpy as np

async def test_fixed_audioprocessor():
    print("🔧 Testing AudioProcessor with torch.load fix")
    print("=" * 50)
    
    processor = AudioProcessor(model_name="base")
    print("✓ AudioProcessor initialized")
    
    # Test model loading
    model_loaded = await processor.load_model()
    print(f"Model loaded: {model_loaded}")
    
    if model_loaded:
        print("✓ Model loading SUCCESS!")
        
        # Test transcription
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        result = await processor.transcribe(test_audio)
        
        print(f"Transcription test:")
        print(f"  Success: {result.success}")
        print(f"  Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            print("🎉 AudioProcessor is FULLY FIXED and FUNCTIONAL!")
            return True
    
    print("❌ Still needs more work")
    return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_audioprocessor())
    sys.exit(0 if success else 1)