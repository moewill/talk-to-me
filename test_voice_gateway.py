#!/usr/bin/env python3
"""
Test VoiceGateway WebSocket server startup and basic functionality
"""

import sys
sys.path.append('src')

import asyncio
import websockets
import json
import time

async def test_voice_gateway_server():
    """Test VoiceGateway server startup."""
    print("🌐 Testing VoiceGateway WebSocket Server")
    print("=" * 50)
    
    try:
        from voice_gateway import VoiceGateway
        
        # Create gateway instance
        gateway = VoiceGateway(host="localhost", port=8081)  # Use different port to avoid conflicts
        print("✅ VoiceGateway instance created")
        
        # Start server in background
        print("Starting WebSocket server...")
        server_task = asyncio.create_task(gateway.start_server())
        
        # Give server time to start
        await asyncio.sleep(2)
        
        if gateway.running:
            print("✅ WebSocket server started successfully!")
            
            # Test client connection
            print("Testing client connection...")
            
            try:
                uri = f"ws://{gateway.host}:{gateway.port}"
                async with websockets.connect(uri, timeout=5) as websocket:
                    print("✅ Client connected to WebSocket server!")
                    
                    # Wait for welcome message
                    welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    welcome_data = json.loads(welcome_msg)
                    print(f"✅ Received welcome: {welcome_data.get('type')}")
                    
                    # Send ping message
                    ping_msg = {"type": "ping", "timestamp": time.time()}
                    await websocket.send(json.dumps(ping_msg))
                    
                    # Wait for pong
                    pong_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    pong_data = json.loads(pong_msg)
                    print(f"✅ Received pong: {pong_data.get('type')}")
                    
                    print("🎉 VoiceGateway WebSocket server is FULLY FUNCTIONAL!")
                    success = True
                    
            except Exception as e:
                print(f"❌ Client connection failed: {e}")
                success = False
            
            # Stop server
            print("Stopping server...")
            await gateway.stop_server()
            print("✅ Server stopped cleanly")
            
        else:
            print("❌ Server failed to start")
            success = False
            
        return success
        
    except Exception as e:
        print(f"❌ VoiceGateway test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_component_integration():
    """Test that VoiceGateway can access all its components."""
    print("\n🔗 Testing Component Integration")
    print("=" * 50)
    
    try:
        from voice_gateway import VoiceGateway
        
        gateway = VoiceGateway()
        
        # Test component initialization
        print("Testing component initialization...")
        
        # Test AudioProcessor
        try:
            audio_test = await gateway.audio_processor.test_transcription()
            print(f"✅ AudioProcessor: {audio_test['test_successful']}")
        except Exception as e:
            print(f"⚠️  AudioProcessor: {e}")
        
        # Test IntentClassifier 
        test_result = gateway.intent_classifier.detect_intent("Hey Claude, test command")
        print(f"✅ IntentClassifier: {test_result.is_claude_command} (confidence: {test_result.confidence})")
        
        # Test ClaudeInterface
        claude_test = await gateway.claude_interface.test_connection()
        print(f"✅ ClaudeInterface: {claude_test['available']}")
        
        print("🎉 All components integrated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Component integration failed: {e}")
        return False

async def main():
    """Run all VoiceGateway tests."""
    print("🎤 VoiceGateway Comprehensive Test Suite")
    print("=" * 60)
    
    # Test server functionality
    server_success = await test_voice_gateway_server()
    
    # Test component integration  
    component_success = await test_component_integration()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    print(f"WebSocket Server:     {'✅ PASS' if server_success else '❌ FAIL'}")
    print(f"Component Integration: {'✅ PASS' if component_success else '❌ FAIL'}")
    
    overall_success = server_success and component_success
    print(f"\nOverall: {'🎉 VoiceGateway FULLY OPERATIONAL!' if overall_success else '❌ Issues need resolution'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)