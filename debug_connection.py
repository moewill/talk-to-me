#!/usr/bin/env python3
"""
Debug WebSocket connection issues.
"""

import asyncio
import json
import websockets

async def test_connection():
    """Test basic WebSocket connection."""
    uri = "ws://localhost:8080/voice"
    
    try:
        print(f"Connecting to {uri}...")
        websocket = await websockets.connect(uri)
        print("Connected!")
        
        # Wait for welcome message
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Received: {message}")
            
            # Try to send a simple message
            test_msg = {"type": "ping"}
            await websocket.send(json.dumps(test_msg))
            print("Sent ping")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Response: {response}")
            
        except asyncio.TimeoutError:
            print("Timeout waiting for message")
        except Exception as e:
            print(f"Error during communication: {e}")
        
        await websocket.close()
        print("Disconnected")
        
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())