#!/usr/bin/env python3
"""
Full demo script for the voice-driven Claude CLI automation system.
This demo starts the WebSocket server and includes a test client.
"""

import asyncio
import json
import logging
import signal
import sys
import wave
from pathlib import Path
from typing import Optional

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voice_gateway import VoiceGateway

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceGatewayDemo:
    """Demonstration of the complete voice gateway system."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.gateway: Optional[VoiceGateway] = None
        self.server_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
    async def start_server(self):
        """Start the WebSocket server."""
        try:
            # Initialize the voice gateway
            self.gateway = VoiceGateway()
            logger.info(f"Starting voice gateway server on {self.host}:{self.port}")
            
            # Start the server
            self.server_task = asyncio.create_task(
                self.gateway.start_server(host=self.host, port=self.port)
            )
            
            logger.info("Voice gateway server started successfully!")
            logger.info(f"WebSocket endpoint: ws://{self.host}:{self.port}")
            logger.info("Server is ready to accept connections.")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
            
    async def stop_server(self):
        """Stop the WebSocket server."""
        logger.info("Shutting down voice gateway server...")
        
        if self.gateway:
            await self.gateway.stop_server()
            
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
                
        self.shutdown_event.set()
        logger.info("Server shutdown complete.")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop_server())

async def create_test_audio_data() -> bytes:
    """Create test audio data for demonstration."""
    # Generate a simple sine wave (440 Hz for 2 seconds)
    sample_rate = 16000
    duration = 2.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    return audio_data.tobytes()

async def test_websocket_client(host: str = "localhost", port: int = 8080):
    """Test WebSocket client that connects to the voice gateway."""
    import websockets
    
    uri = f"ws://{host}:{port}"
    logger.info(f"Connecting to WebSocket server at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server!")
            
            # Send a test message
            test_message = {
                "type": "test",
                "message": "Hello from test client!"
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("Sent test message to server")
            
            # Send some test audio data
            audio_data = await create_test_audio_data()
            await websocket.send(audio_data)
            logger.info("Sent test audio data to server")
            
            # Wait for responses
            timeout = 5.0
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                if isinstance(response, str):
                    logger.info(f"Received text response: {response}")
                else:
                    logger.info(f"Received binary response: {len(response)} bytes")
            except asyncio.TimeoutError:
                logger.info("No response received within timeout")
                
            logger.info("WebSocket client test completed")
            
    except Exception as e:
        logger.error(f"WebSocket client error: {e}")

async def run_integration_test():
    """Run a comprehensive integration test."""
    logger.info("Starting integration test...")
    
    # Test individual components first
    logger.info("Testing individual components...")
    
    # Import and test audio processor
    from audio_processor import AudioProcessor
    audio_processor = AudioProcessor()
    logger.info("AudioProcessor initialized successfully")
    
    # Import and test intent classifier
    from intent_classifier import IntentClassifier
    intent_classifier = IntentClassifier()
    test_text = "Hey Claude, write a simple hello world program"
    result = intent_classifier.classify_intent(test_text)
    logger.info(f"Intent classification test: {result}")
    
    # Import and test Claude interface
    from claude_interface import ClaudeInterface
    claude_interface = ClaudeInterface()
    is_available = await claude_interface.check_claude_availability()
    logger.info(f"Claude CLI availability: {is_available}")
    
    if is_available:
        logger.info("Running simple Claude command test...")
        response = await claude_interface.execute_command("echo 'Integration test successful'")
        logger.info(f"Claude response: {response.output[:100]}...")
    else:
        logger.warning("Claude CLI not available - skipping Claude command test")
    
    logger.info("Integration test completed successfully!")

async def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voice Gateway Demo")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("--mode", choices=["server", "client", "test", "full"], 
                       default="full", help="Demo mode")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        # Run server only
        demo = VoiceGatewayDemo(args.host, args.port)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, demo.signal_handler)
        signal.signal(signal.SIGTERM, demo.signal_handler)
        
        await demo.start_server()
        
    elif args.mode == "client":
        # Run client only (assumes server is running)
        await test_websocket_client(args.host, args.port)
        
    elif args.mode == "test":
        # Run integration test only
        await run_integration_test()
        
    elif args.mode == "full":
        # Run full demo (server + client + test)
        logger.info("Starting full demo...")
        
        # Run integration test first
        await run_integration_test()
        
        # Start server in background
        demo = VoiceGatewayDemo(args.host, args.port)
        server_task = asyncio.create_task(demo.start_server())
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Run client test
        client_task = asyncio.create_task(test_websocket_client(args.host, args.port))
        
        try:
            # Wait for client to complete
            await client_task
            
            # Let server run a bit longer
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
            
        finally:
            # Clean shutdown
            await demo.stop_server()
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Full demo completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)
