#!/usr/bin/env python3
"""
WebSocket client demo for testing the voice gateway server.
This client can send text messages and audio data to test the real-time processing pipeline.
"""

import asyncio
import json
import logging
import sys
import wave
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import websockets
except ImportError:
    print("websockets library not found. Install with: pip install websockets")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceGatewayClient:
    """WebSocket client for testing the voice gateway."""
    
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            logger.info(f"Connecting to {self.uri}")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            logger.info("Connected successfully!")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from server")
            
    async def send_text_message(self, message_type: str, content: str):
        """Send a text message to the server."""
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return False
            
        try:
            message = {
                "type": message_type,
                "content": content,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent {message_type} message: {content}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            return False
            
    async def send_audio_data(self, audio_data: bytes):
        """Send audio data to the server."""
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return False
            
        try:
            await self.websocket.send(audio_data)
            logger.info(f"Sent audio data: {len(audio_data)} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio data: {e}")
            return False
            
    async def receive_messages(self, timeout: float = 5.0):
        """Receive messages from the server."""
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return None
            
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            
            if isinstance(response, str):
                try:
                    data = json.loads(response)
                    logger.info(f"Received JSON message: {data}")
                    return data
                except json.JSONDecodeError:
                    logger.info(f"Received text message: {response}")
                    return response
            else:
                logger.info(f"Received binary message: {len(response)} bytes")
                return response
                
        except asyncio.TimeoutError:
            logger.warning(f"No response received within {timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

def generate_test_audio(frequency: float = 440.0, duration: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate test audio data (sine wave)."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    return audio_data.tobytes()

def create_voice_command_audio() -> bytes:
    """Create audio that simulates a voice command."""
    # This is a placeholder - in a real scenario, this would be actual recorded speech
    # For now, we'll generate a simple tone burst pattern
    sample_rate = 16000
    duration = 3.0
    
    # Create a pattern that might represent speech cadence
    times = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.zeros_like(times)
    
    # Add some frequency variations to simulate speech
    for i, freq in enumerate([200, 300, 250, 400, 350]):
        start_idx = int(i * len(times) / 5)
        end_idx = int((i + 1) * len(times) / 5)
        segment = np.sin(2 * np.pi * freq * times[start_idx:end_idx])
        audio[start_idx:end_idx] = segment * 0.5
    
    # Convert to 16-bit PCM
    audio = (audio * 32767).astype(np.int16)
    return audio.tobytes()

async def automated_client_demo(uri: str):
    """Automated client demo that runs a series of tests."""
    client = VoiceGatewayClient(uri)
    
    if not await client.connect():
        return
        
    logger.info("Running automated client demo...")
    
    # Test 1: Send hello message
    logger.info("Test 1: Sending hello message")
    await client.send_text_message("greeting", "Hello, voice gateway!")
    response1 = await client.receive_messages()
    
    # Test 2: Send test audio
    logger.info("Test 2: Sending test audio")
    audio_data = generate_test_audio(frequency=880.0, duration=1.5)
    await client.send_audio_data(audio_data)
    response2 = await client.receive_messages()
    
    # Test 3: Send simulated Claude command
    logger.info("Test 3: Sending simulated Claude command")
    command_audio = create_voice_command_audio()
    await client.send_audio_data(command_audio)
    response3 = await client.receive_messages(timeout=15.0)  # Longer timeout for Claude
    
    # Test 4: Send status request
    logger.info("Test 4: Requesting server status")
    await client.send_text_message("status_request", "What's your current status?")
    response4 = await client.receive_messages()
    
    # Summarize results
    logger.info("Automated demo completed!")
    logger.info(f"Test 1 response: {'✓' if response1 else '✗'}")
    logger.info(f"Test 2 response: {'✓' if response2 else '✗'}")
    logger.info(f"Test 3 response: {'✓' if response3 else '✗'}")
    logger.info(f"Test 4 response: {'✓' if response4 else '✗'}")
    
    await client.disconnect()

async def main():
    """Main function for the WebSocket client demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voice Gateway WebSocket Client Demo")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("--mode", choices=["automated"], 
                       default="automated", help="Demo mode")
    
    args = parser.parse_args()
    
    uri = f"ws://{args.host}:{args.port}"
    
    try:
        if args.mode == "automated":
            await automated_client_demo(uri)
            
    except Exception as e:
        logger.error(f"Client demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
