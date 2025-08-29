#!/usr/bin/env python3
"""
Test minimal reproduction of Whisper model loading issue.
"""

import traceback

def test_basic_import():
    """Test basic Whisper import."""
    print("Testing basic Whisper import...")
    try:
        import whisper
        print(f"✓ Whisper imported successfully from: {whisper.__file__}")
        print(f"✓ load_model available: {'load_model' in dir(whisper)}")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_model_loading_basic():
    """Test basic model loading without any fixes."""
    print("\nTesting basic model loading...")
    try:
        import whisper
        model = whisper.load_model("tiny")
        print("✓ Basic model loading successful")
        return True
    except Exception as e:
        print(f"✗ Basic model loading failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def test_model_loading_with_device():
    """Test model loading with explicit device."""
    print("\nTesting model loading with device specification...")
    try:
        import whisper
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        model = whisper.load_model("tiny", device=device)
        print("✓ Model loading with device successful")
        return True
    except Exception as e:
        print(f"✗ Model loading with device failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def test_torch_load_patch():
    """Test the torch.load patch approach."""
    print("\nTesting torch.load patch approach...")
    try:
        import whisper
        import torch
        
        # Save original torch.load
        original_load = torch.load
        
        def patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        # Apply patch
        torch.load = patched_load
        
        try:
            model = whisper.load_model("tiny")
            print("✓ Patched model loading successful")
            return True
        finally:
            # Restore original
            torch.load = original_load
            
    except Exception as e:
        print(f"✗ Patched model loading failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=== Whisper Model Loading Diagnostic ===\n")
    
    results = []
    results.append(test_basic_import())
    results.append(test_model_loading_basic())
    results.append(test_model_loading_with_device())
    results.append(test_torch_load_patch())
    
    print(f"\n=== Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("All tests passed - Whisper is working correctly!")
    else:
        print("Some tests failed - further investigation needed.")

if __name__ == "__main__":
    main()