"""
AudioProcessor Factory - Workaround for Whisper model loading issues
Creates AudioProcessor instances with pre-loaded models to bypass loading problems.
"""

import whisper
import torch
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

def create_audio_processor(model_name: str = "base", device: str = "auto") -> AudioProcessor:
    """
    Create an AudioProcessor with a pre-loaded Whisper model.
    
    This factory function works around the torch.load pickle issues by loading
    the model externally and injecting it into the AudioProcessor.
    
    Args:
        model_name: Whisper model size ("tiny", "base", "small", "medium", "large")
        device: Device to run on ("cpu", "cuda", or "auto")
        
    Returns:
        AudioProcessor instance with loaded model
        
    Raises:
        Exception: If model loading fails
    """
    
    # Apply torch.load patch globally for Whisper compatibility
    original_load = torch.load
    
    def whisper_compatible_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    
    torch.load = whisper_compatible_load
    
    try:
        # Load model directly using Whisper
        logger.info(f"Loading Whisper model '{model_name}' via factory...")
        model = whisper.load_model(model_name, device=device)
        
        # Create AudioProcessor instance
        processor = AudioProcessor(model_name=model_name, device=device)
        
        # Inject the pre-loaded model
        processor.model = model
        processor.model_loaded = True
        
        logger.info(f"AudioProcessor created successfully with {model_name} model")
        return processor
        
    except Exception as e:
        logger.error(f"Failed to create AudioProcessor: {e}")
        raise
    finally:
        # Restore original torch.load
        torch.load = original_load

async def test_audio_processor_factory():
    """Test the AudioProcessor factory."""
    import asyncio
    import numpy as np
    
    print("🏭 Testing AudioProcessor Factory")
    print("=" * 40)
    
    try:
        # Create processor with factory
        processor = create_audio_processor("base")
        print("✓ AudioProcessor created via factory")
        
        # Test transcription
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second silence
        result = await processor.transcribe(test_audio)
        
        print(f"Transcription test:")
        print(f"  Success: {result.success}")
        print(f"  Text: '{result.text}'")
        print(f"  Processing time: {result.processing_time:.2f}s")
        
        if result.success:
            print("🎉 AudioProcessor Factory WORKING!")
            return True
        else:
            print(f"❌ Transcription failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    import sys
    success = asyncio.run(test_audio_processor_factory())
    sys.exit(0 if success else 1)