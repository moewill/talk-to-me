#!/usr/bin/env python3
"""
Dependency Validation Script for Voice-Driven Claude CLI
Tests all critical dependencies to ensure system is ready for operation.
"""

import sys
import importlib
import subprocess
from typing import Dict, List, Tuple, Optional

def test_import(module_name: str, alias: Optional[str] = None) -> Tuple[bool, str]:
    """Test if a module can be imported successfully."""
    try:
        if alias:
            module = importlib.import_module(module_name)
            return True, f"✓ {module_name} (as {alias}): {getattr(module, '__version__', 'unknown version')}"
        else:
            module = importlib.import_module(module_name)
            return True, f"✓ {module_name}: {getattr(module, '__version__', 'unknown version')}"
    except ImportError as e:
        return False, f"✗ {module_name}: FAILED - {e}"
    except Exception as e:
        return False, f"✗ {module_name}: ERROR - {e}"

def test_whisper_model_loading() -> Tuple[bool, str]:
    """Test Whisper model loading specifically."""
    try:
        import whisper
        model = whisper.load_model("base")
        return True, f"✓ Whisper model loading: SUCCESS (model type: {type(model).__name__})"
    except Exception as e:
        return False, f"✗ Whisper model loading: FAILED - {e}"

def test_claude_cli() -> Tuple[bool, str]:
    """Test Claude CLI availability."""
    try:
        result = subprocess.run(['claude', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            return True, f"✓ Claude CLI: Available ({version})"
        else:
            return False, f"✗ Claude CLI: Exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "✗ Claude CLI: TIMEOUT (command hangs)"
    except FileNotFoundError:
        return False, "✗ Claude CLI: NOT FOUND in PATH"
    except Exception as e:
        return False, f"✗ Claude CLI: ERROR - {e}"

def test_ffmpeg() -> Tuple[bool, str]:
    """Test FFmpeg availability."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\\n')[0]
            return True, f"✓ FFmpeg: Available ({first_line})"
        else:
            return False, f"✗ FFmpeg: Exit code {result.returncode}"
    except FileNotFoundError:
        return False, "✗ FFmpeg: NOT FOUND (install with 'brew install ffmpeg')"
    except subprocess.TimeoutExpired:
        return False, "✗ FFmpeg: TIMEOUT"
    except Exception as e:
        return False, f"✗ FFmpeg: ERROR - {e}"

def check_numpy_version() -> Tuple[bool, str]:
    """Check NumPy version specifically for compatibility."""
    try:
        import numpy as np
        version = np.__version__
        major, minor = version.split('.')[:2]
        if int(major) >= 2:
            return False, f"✗ NumPy: {version} (INCOMPATIBLE - needs <2.0 for Whisper)"
        else:
            return True, f"✓ NumPy: {version} (COMPATIBLE)"
    except Exception as e:
        return False, f"✗ NumPy: ERROR - {e}"

def main():
    """Run comprehensive dependency validation."""
    print("🔍 Voice-Driven Claude CLI - Dependency Validation")
    print("=" * 60)
    
    # Core Python dependencies
    critical_modules = [
        'numpy',
        'torch', 
        'whisper',
        'websockets',
        'pydub',
        'soundfile',
        'asyncio'
    ]
    
    # Optional but recommended
    optional_modules = [
        'aiohttp',
        'pytest',
        'regex'
    ]
    
    results = []
    
    print("\\n📦 Critical Dependencies:")
    print("-" * 30)
    
    # Test NumPy version specifically
    success, msg = check_numpy_version()
    results.append(success)
    print(msg)
    
    # Test other critical modules
    for module in critical_modules:
        if module != 'numpy':  # Already tested above
            success, msg = test_import(module)
            results.append(success)
            print(msg)
    
    print("\\n🎤 Audio Processing:")
    print("-" * 30)
    
    # Test Whisper model loading
    success, msg = test_whisper_model_loading()
    results.append(success)
    print(msg)
    
    # Test FFmpeg
    success, msg = test_ffmpeg()
    results.append(success)
    print(msg)
    
    print("\\n🤖 Claude Integration:")
    print("-" * 30)
    
    # Test Claude CLI
    success, msg = test_claude_cli()
    results.append(success)
    print(msg)
    
    print("\\n📚 Optional Dependencies:")
    print("-" * 30)
    
    optional_results = []
    for module in optional_modules:
        success, msg = test_import(module)
        optional_results.append(success)
        print(msg)
    
    print("\\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY:")
    print("=" * 60)
    
    critical_passed = sum(results)
    critical_total = len(results)
    optional_passed = sum(optional_results)
    optional_total = len(optional_results)
    
    print(f"Critical Dependencies: {critical_passed}/{critical_total} ({'✓ PASS' if critical_passed == critical_total else '✗ FAIL'})")
    print(f"Optional Dependencies: {optional_passed}/{optional_total}")
    
    if critical_passed == critical_total:
        print("\\n🎉 ALL CRITICAL DEPENDENCIES VALIDATED!")
        print("   System is ready for Voice-Driven Claude CLI operation.")
        return 0
    else:
        print("\\n❌ CRITICAL DEPENDENCIES MISSING!")
        print("   System is NOT ready. Fix the failed dependencies above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())