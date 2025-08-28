#!/usr/bin/env python3
"""
Super simple voice gateway for debugging.
"""

import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def handle_connection(websocket: WebSocketServerProtocol, path: str):
    """Handle WebSocket connection with minimal processing."""
    logger.info(f"New connection from {websocket.remote_address}")
    
    try:
        # Send welcome message
        welcome = {
            "type": "welcome",
            "connection_id": "test_conn",
            "status": "connected"
        }
        await websocket.send(json.dumps(welcome))
        logger.info("Welcome message sent")
        
        # Process messages
        async for message in websocket:
            logger.info(f"Received: {type(message)} - {message}")
            
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    response = {"type": "echo", "data": data}
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(f"Echo: {message}")
            else:
                await websocket.send(f"Received {len(message)} bytes")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Start simple voice gateway."""
    logger.info("Starting simple voice gateway on localhost:8082")
    
    server = await websockets.serve(handle_connection, "localhost", 8082)
    logger.info("Server started")
    
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())