#!/usr/bin/env python3
"""
Debug Claude CLI timeout issues and test different execution approaches
"""

import sys
sys.path.append('src')

import asyncio
import subprocess
import time

async def test_claude_direct():
    """Test Claude CLI directly with subprocess."""
    print("🔍 Testing Claude CLI Direct Execution")
    print("=" * 40)
    
    commands = [
        "Hello",
        "What is 2+2?", 
        "Tell me a short joke"
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\nTest {i}: '{cmd}'")
        print("-" * 20)
        
        try:
            start_time = time.time()
            
            # Test with shorter timeout and different approaches
            result = subprocess.run(
                ['claude', cmd], 
                capture_output=True, 
                text=True, 
                timeout=8,  # Reduced timeout
                shell=False
            )
            
            execution_time = time.time() - start_time
            
            print(f"Exit code: {result.returncode}")
            print(f"Execution time: {execution_time:.2f}s")
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"Output: {output[:100]}{'...' if len(output) > 100 else ''}")
                print("✅ SUCCESS")
            else:
                print(f"Error: {result.stderr}")
                print("❌ FAILED")
                
        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT (8 seconds)")
        except Exception as e:
            print(f"❌ ERROR: {e}")

async def test_claude_interface():
    """Test ClaudeInterface with different configurations."""
    print("\n🔧 Testing ClaudeInterface Class")
    print("=" * 40)
    
    from claude_interface import ClaudeInterface
    
    # Test with shorter timeout
    interface = ClaudeInterface(timeout=5)
    
    commands = ["Hello", "2+2=?"]
    
    for cmd in commands:
        print(f"\nTesting: '{cmd}'")
        try:
            start_time = time.time()
            result = await interface.execute_command(cmd)
            execution_time = time.time() - start_time
            
            print(f"Success: {result.success}")
            print(f"Time: {execution_time:.2f}s")
            
            if result.success:
                print(f"Output: {result.output[:50]}...")
                print("✅ SUCCESS")
            else:
                print(f"Error: {result.error}")
                print("❌ FAILED")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

async def test_optimized_claude():
    """Test optimized Claude execution approach."""
    print("\n⚡ Testing Optimized Claude Execution")
    print("=" * 40)
    
    try:
        # Test minimal command that should be fast
        minimal_cmd = "Hi"
        
        print(f"Testing minimal command: '{minimal_cmd}'")
        
        start_time = time.time()
        
        # Use Popen for more control
        process = subprocess.Popen(
            ['claude', minimal_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.to_thread(process.communicate),
                timeout=3.0  # Very short timeout
            )
            
            execution_time = time.time() - start_time
            
            print(f"Return code: {process.returncode}")
            print(f"Execution time: {execution_time:.2f}s")
            
            if process.returncode == 0:
                print(f"Output: {stdout.strip()}")
                print("✅ OPTIMIZED APPROACH WORKS!")
                return True
            else:
                print(f"Error: {stderr}")
                
        except asyncio.TimeoutError:
            print("❌ Still timing out even with minimal command")
            process.terminate()
            await asyncio.sleep(0.1)
            process.kill()
            
        return False
        
    except Exception as e:
        print(f"❌ Optimized test failed: {e}")
        return False

async def main():
    """Run all Claude timeout debugging tests."""
    print("🕵️ Claude CLI Timeout Debugging Suite")
    print("=" * 60)
    
    # Test 1: Direct subprocess calls
    await test_claude_direct()
    
    # Test 2: ClaudeInterface class
    await test_claude_interface()
    
    # Test 3: Optimized approach
    success = await test_optimized_claude()
    
    print("\n" + "=" * 60)
    print("🎯 DEBUGGING CONCLUSIONS:")
    print("=" * 60)
    
    if success:
        print("✅ Found working approach for Claude execution!")
    else:
        print("❌ Claude CLI appears to have fundamental timeout issues")
        print("   Recommendation: Use shorter timeouts and implement retries")

if __name__ == "__main__":
    asyncio.run(main())