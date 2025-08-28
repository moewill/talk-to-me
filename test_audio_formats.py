#!/usr/bin/env python3
"""
Test audio format conversion with working FFmpeg
"""

import sys
sys.path.append('src')

import asyncio
import numpy as np
import tempfile
import os
import wave
import subprocess

def test_ffmpeg_direct():
    """Test FFmpeg directly with audio conversion."""
    print("🎵 Testing FFmpeg Audio Conversion")
    print("=" * 40)
    
    try:
        # Create test WAV file
        sample_rate = 16000
        duration = 2.0
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Write WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
            
        with wave.open(wav_path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(audio_data.tobytes())
        
        print(f"✓ Created test WAV file: {os.path.basename(wav_path)}")
        
        # Test FFmpeg conversion to MP3
        mp3_path = wav_path.replace('.wav', '.mp3')
        
        result = subprocess.run([
            'ffmpeg', '-i', wav_path, '-acodec', 'mp3', '-y', mp3_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ FFmpeg WAV → MP3 conversion successful")
            
            # Check file sizes
            wav_size = os.path.getsize(wav_path)
            mp3_size = os.path.getsize(mp3_path)
            print(f"  WAV size: {wav_size} bytes")
            print(f"  MP3 size: {mp3_size} bytes")
            
            # Test conversion back to WAV
            wav2_path = wav_path.replace('.wav', '_converted.wav')
            result2 = subprocess.run([
                'ffmpeg', '-i', mp3_path, '-acodec', 'pcm_s16le', '-y', wav2_path
            ], capture_output=True, text=True, timeout=10)
            
            if result2.returncode == 0:
                print("✓ FFmpeg MP3 → WAV conversion successful")
                success = True
            else:
                print(f"❌ MP3 → WAV failed: {result2.stderr}")
                success = False
        else:
            print(f"❌ WAV → MP3 failed: {result.stderr}")
            success = False
            
        # Cleanup
        for path in [wav_path, mp3_path, wav2_path]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass
                
        return success
        
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        return False

def test_pydub_with_ffmpeg():
    """Test pydub with FFmpeg backend."""
    print("\n🔊 Testing Pydub with FFmpeg")
    print("=" * 40)
    
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # Generate test audio with pydub
        tone = Sine(440).to_audio_segment(duration=2000)  # 2 seconds
        print("✓ Generated sine wave with pydub")
        
        # Test export to different formats
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
            
        tone.export(wav_path, format="wav")
        print("✓ Exported to WAV format")
        
        # Test loading and conversion
        audio = AudioSegment.from_wav(wav_path)
        print(f"✓ Loaded audio: {len(audio)}ms, {audio.frame_rate}Hz")
        
        # Test MP3 export (requires FFmpeg)
        mp3_path = wav_path.replace('.wav', '.mp3')
        audio.export(mp3_path, format="mp3")
        print("✓ Exported to MP3 format")
        
        # Test loading MP3 back
        audio_mp3 = AudioSegment.from_mp3(mp3_path)
        print(f"✓ Loaded MP3: {len(audio_mp3)}ms, {audio_mp3.frame_rate}Hz")
        
        # Cleanup
        for path in [wav_path, mp3_path]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass
                
        return True
        
    except Exception as e:
        print(f"❌ Pydub test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_soundfile():
    """Test soundfile library."""
    print("\n🎧 Testing SoundFile")
    print("=" * 40)
    
    try:
        import soundfile as sf
        
        # Generate test data
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        
        # Test write and read
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
            
        sf.write(wav_path, audio_data, sample_rate)
        print("✓ Wrote audio with soundfile")
        
        # Read it back
        data, sr = sf.read(wav_path)
        print(f"✓ Read audio: {len(data)} samples at {sr}Hz")
        
        # Cleanup
        os.unlink(wav_path)
        
        return True
        
    except Exception as e:
        print(f"❌ SoundFile test failed: {e}")
        return False

def main():
    """Run all audio format tests."""
    print("🎤 Audio Format Conversion Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test FFmpeg directly
    results.append(("FFmpeg Direct", test_ffmpeg_direct()))
    
    # Test pydub with FFmpeg
    results.append(("Pydub + FFmpeg", test_pydub_with_ffmpeg()))
    
    # Test soundfile
    results.append(("SoundFile", test_soundfile()))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not success:
            all_passed = False
    
    print(f"\nOverall: {'🎉 ALL TESTS PASSED!' if all_passed else '❌ Some tests failed'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())