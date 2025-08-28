#!/usr/bin/env python3
"""
Minimal WebSocket server for debugging connection issues.
"""

import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def handle_client(websocket: WebSocketServerProtocol, path: str):
    """Handle a WebSocket client connection."""
    logger.info(f"New connection from {websocket.remote_address} on path {path}")
    
    try:
        # Send welcome message
        welcome = {
            "type": "welcome",
            "message": "Minimal WebSocket server connected",
            "timestamp": asyncio.get_event_loop().time()
        }
        await websocket.send(json.dumps(welcome))
        logger.info("Sent welcome message")
        
        # Echo messages back
        async for message in websocket:
            logger.info(f"Received message: {type(message)} - {len(str(message))} chars")
            
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    logger.info(f"Parsed JSON: {data}")
                    
                    response = {
                        "type": "echo",
                        "original": data,
                        "timestamp": asyncio.get_event_loop().time()
                    }
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    logger.info(f"Received text: {message}")
                    await websocket.send(f"Echo: {message}")
                    
            else:
                # Binary data
                logger.info(f"Received binary data: {len(message)} bytes")
                await websocket.send(f"Received {len(message)} bytes of binary data")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"Error handling client: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Start the minimal WebSocket server."""
    host = "localhost"
    port = 8081
    
    logger.info(f"Starting minimal WebSocket server on {host}:{port}")
    
    server = await websockets.serve(
        handle_client,
        host,
        port,
        ping_interval=20,
        ping_timeout=10
    )
    
    logger.info("Server started successfully")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())