"""
Voice Gateway for Voice-driven Claude CLI automation system.

This module provides the main WebSocket server that orchestrates the entire
voice-to-Claude pipeline. It handles incoming audio streams, coordinates
speech-to-text processing, intent classification, and Claude CLI execution.
"""

import asyncio
import json
import logging
import time
import traceback
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.server import WebSocketServerProtocol

# Import our custom modules
from audio_processor import AudioProcessor, TranscriptionResult
from claude_interface import ClaudeInterface, ClaudeResponse
from intent_classifier import IntentClassifier, IntentResult

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocketServerProtocol
    connection_id: str
    connected_at: float
    last_activity: float
    processed_messages: int


@dataclass
class ProcessingStats:
    """Statistics for the voice gateway processing."""
    total_connections: int
    active_connections: int
    total_audio_processed: int
    total_claude_commands: int
    successful_claude_commands: int
    average_processing_time: float
    uptime_start: float


class VoiceGateway:
    """
    Main WebSocket server for voice-driven Claude CLI automation.
    
    Coordinates audio processing, intent classification, and Claude execution
    in a real-time voice conversation pipeline.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        whisper_model: str = "base",
        claude_binary: str = "claude"
    ):
        """
        Initialize the Voice Gateway.
        
        Args:
            host: Host to bind the WebSocket server
            port: Port to bind the WebSocket server
            whisper_model: Whisper model to use for speech-to-text
            claude_binary: Path to Claude CLI binary
        """
        self.host = host
        self.port = port
        
        # Initialize core components
        self.audio_processor = AudioProcessor(model_name=whisper_model)
        self.intent_classifier = IntentClassifier()
        self.claude_interface = ClaudeInterface(claude_binary=claude_binary)
        
        # Connection management
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.connection_counter = 0
        
        # Statistics tracking
        self.stats = ProcessingStats(
            total_connections=0,
            active_connections=0,
            total_audio_processed=0,
            total_claude_commands=0,
            successful_claude_commands=0,
            average_processing_time=0.0,
            uptime_start=time.time()
        )
        
        # Configuration
        self.max_connections = 10
        self.max_message_size = 10 * 1024 * 1024  # 10MB
        self.heartbeat_interval = 30  # seconds
        
        # Server state
        self.server = None
        self.running = False

    async def start_server(self) -> None:
        """Start the WebSocket server."""
        try:
            logger.info(f"Initializing Voice Gateway components...")
            
            # Pre-load the Whisper model
            model_loaded = await self.audio_processor.load_model()
            if not model_loaded:
                logger.warning("Failed to load Whisper model - audio processing may fail")
            
            # Test Claude CLI connection
            claude_test = await self.claude_interface.test_connection()
            if not claude_test['available']:
                logger.warning("Claude CLI not available - commands will fail")
            else:
                logger.info("Claude CLI connection successful")
            
            # Start WebSocket server
            logger.info(f"Starting Voice Gateway server on {self.host}:{self.port}")
            
            self.server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                max_size=self.max_message_size,
                ping_interval=self.heartbeat_interval,
                ping_timeout=10
            )
            
            self.running = True
            logger.info(f"Voice Gateway server started successfully")
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_task())
            asyncio.create_task(self._stats_logger_task())
            
        except Exception as e:
            logger.error(f"Failed to start Voice Gateway server: {e}")
            raise

    async def stop_server(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            logger.info("Stopping Voice Gateway server...")
            self.running = False
            
            # Close all active connections
            for connection_info in list(self.active_connections.values()):
                try:
                    await connection_info.websocket.close()
                except:
                    pass
            
            self.server.close()
            await self.server.wait_closed()
            logger.info("Voice Gateway server stopped")

    async def handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """
        Handle a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
        """
        connection_id = f"conn_{self.connection_counter}"
        self.connection_counter += 1
        
        # Check connection limits
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"Connection limit reached, rejecting {connection_id}")
            await websocket.close(code=1013, reason="Server overloaded")
            return
        
        # Create connection info
        connection_info = ConnectionInfo(
            websocket=websocket,
            connection_id=connection_id,
            connected_at=time.time(),
            last_activity=time.time(),
            processed_messages=0
        )
        
        self.active_connections[connection_id] = connection_info
        self.stats.total_connections += 1
        self.stats.active_connections = len(self.active_connections)
        
        logger.info(f"New connection: {connection_id} from {websocket.remote_address}")
        
        try:
            logger.debug(f"[{connection_id}] About to send welcome message")
            # Send welcome message
            await self._send_message(websocket, {
                "type": "welcome",
                "connection_id": connection_id,
                "status": "connected",
                "capabilities": {
                    "speech_to_text": False,  # Hardcode to avoid any audio processor issues
                    "claude_cli": True,
                    "supported_formats": ["wav", "mp3", "raw_pcm"]
                }
            })
            logger.debug(f"[{connection_id}] Welcome message sent successfully")
            
            logger.debug(f"[{connection_id}] Starting message processing loop")
            # Process messages
            await self._process_messages(connection_info)
            logger.debug(f"[{connection_id}] Message processing loop ended")
            
        except ConnectionClosed as e:
            logger.info(f"Connection {connection_id} closed normally: {e.code} {e.reason}")
        except WebSocketException as e:
            logger.warning(f"WebSocket error for {connection_id}: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            logger.error(f"Unexpected error for {connection_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                self.stats.active_connections = len(self.active_connections)
                logger.info(f"Connection {connection_id} removed")

    async def _process_messages(self, connection_info: ConnectionInfo) -> None:
        """
        Process messages from a WebSocket connection.
        
        Args:
            connection_info: Information about the connection
        """
        websocket = connection_info.websocket
        connection_id = connection_info.connection_id
        
        logger.debug(f"[{connection_id}] Entering message processing loop")
        
        async for message in websocket:
            try:
                logger.debug(f"[{connection_id}] Received message: {type(message)}, size: {len(str(message))}")
                connection_info.last_activity = time.time()
                connection_info.processed_messages += 1
                
                # Handle different message types
                if isinstance(message, str):
                    # JSON message
                    await self._handle_json_message(connection_info, json.loads(message))
                elif isinstance(message, bytes):
                    # Binary audio data
                    await self._handle_audio_message(connection_info, message)
                else:
                    logger.warning(f"Unknown message type from {connection_id}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {connection_id}: {e}")
                await self._send_error(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")
                await self._send_error(websocket, f"Processing error: {str(e)}")

    async def _handle_json_message(self, connection_info: ConnectionInfo, data: Dict[str, Any]) -> None:
        """
        Handle JSON control messages.
        
        Args:
            connection_info: Connection information
            data: Parsed JSON data
        """
        websocket = connection_info.websocket
        message_type = data.get("type")
        logger.debug(f"Handling JSON message type '{message_type}' from {connection_info.connection_id}: {data}")
        
        if message_type == "ping":
            await self._send_message(websocket, {"type": "pong", "timestamp": time.time()})
            
        elif message_type == "get_stats":
            stats = await self._get_comprehensive_stats()
            await self._send_message(websocket, {"type": "stats", "data": stats})
            
        elif message_type == "test_claude":
            test_result = await self.claude_interface.test_connection()
            await self._send_message(websocket, {"type": "claude_test", "data": test_result})
            
        elif message_type == "text_command":
            # Direct text command (for testing)
            text = data.get("text", "")
            if text:
                await self._process_text_command(connection_info, text)
                
        elif message_type == "greeting" or message_type == "text_message":
            # Handle greeting and text messages
            content = data.get("content", "")
            await self._send_message(websocket, {
                "type": "response",
                "message": f"Received: {content}",
                "timestamp": time.time()
            })
            
        else:
            logger.warning(f"Unknown message type '{message_type}' from {connection_info.connection_id}")
            await self._send_message(websocket, {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": time.time()
            })

    async def _handle_audio_message(self, connection_info: ConnectionInfo, audio_data: bytes) -> None:
        """
        Handle binary audio data.
        
        Args:
            connection_info: Connection information
            audio_data: Raw audio data
        """
        start_time = time.time()
        websocket = connection_info.websocket
        
        try:
            # Send processing acknowledgment
            await self._send_message(websocket, {
                "type": "processing",
                "status": "transcribing",
                "audio_size": len(audio_data)
            })
            
            # Transcribe audio
            transcription_result = await self.audio_processor.transcribe(audio_data)
            self.stats.total_audio_processed += 1
            
            if not transcription_result.success:
                await self._send_error(websocket, f"Transcription failed: {transcription_result.error}")
                return
            
            # Send transcription result
            await self._send_message(websocket, {
                "type": "transcription",
                "text": transcription_result.text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.language,
                "processing_time": transcription_result.processing_time
            })
            
            # Process the transcribed text
            if transcription_result.text.strip():
                await self._process_text_command(connection_info, transcription_result.text)
            
            # Update processing time stats
            processing_time = time.time() - start_time
            self._update_processing_time(processing_time)
            
        except Exception as e:
            logger.error(f"Error processing audio from {connection_info.connection_id}: {e}")
            await self._send_error(websocket, f"Audio processing error: {str(e)}")

    async def _process_text_command(self, connection_info: ConnectionInfo, text: str) -> None:
        """
        Process transcribed text for Claude commands.
        
        Args:
            connection_info: Connection information
            text: Transcribed text to process
        """
        websocket = connection_info.websocket
        
        try:
            logger.debug(f"Processing text command: '{text}'")
            # Classify intent
            intent_result = self.intent_classifier.detect_intent(text)
            logger.debug(f"Intent classification result: {intent_result}")
            
            # Send intent classification result
            await self._send_message(websocket, {
                "type": "intent",
                "is_claude_command": intent_result.is_claude_command,
                "command": intent_result.command,
                "confidence": intent_result.confidence,
                "keywords": intent_result.detected_keywords,
                "original_text": intent_result.original_text
            })
            
            # Execute Claude command if detected
            if intent_result.is_claude_command and intent_result.command:
                await self._execute_claude_command(connection_info, intent_result.command)
            
        except Exception as e:
            logger.error(f"Error processing text command: {e}")
            await self._send_error(websocket, f"Command processing error: {str(e)}")

    async def _execute_claude_command(self, connection_info: ConnectionInfo, command: str) -> None:
        """
        Execute a Claude CLI command.
        
        Args:
            connection_info: Connection information
            command: Command to execute
        """
        websocket = connection_info.websocket
        
        try:
            # Send execution start notification
            await self._send_message(websocket, {
                "type": "claude_execution",
                "status": "starting",
                "command": command
            })
            
            # Execute command
            self.stats.total_claude_commands += 1
            claude_result = await self.claude_interface.execute_command(command)
            
            if claude_result.success:
                self.stats.successful_claude_commands += 1
            
            # Send result
            await self._send_message(websocket, {
                "type": "claude_result",
                "success": claude_result.success,
                "output": claude_result.output,
                "error": claude_result.error,
                "execution_time": claude_result.execution_time,
                "command": claude_result.command
            })
            
        except Exception as e:
            logger.error(f"Error executing Claude command: {e}")
            await self._send_error(websocket, f"Claude execution error: {str(e)}")

    async def _send_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """
        Send a JSON message to a WebSocket.
        
        Args:
            websocket: Target WebSocket connection
            data: Data to send
        """
        try:
            message = json.dumps(data)
            await websocket.send(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str) -> None:
        """
        Send an error message to a WebSocket.
        
        Args:
            websocket: Target WebSocket connection
            error_message: Error message to send
        """
        await self._send_message(websocket, {
            "type": "error",
            "message": error_message,
            "timestamp": time.time()
        })

    def _update_processing_time(self, processing_time: float) -> None:
        """Update average processing time statistics."""
        if self.stats.total_audio_processed == 1:
            self.stats.average_processing_time = processing_time
        else:
            # Running average
            total = self.stats.total_audio_processed
            self.stats.average_processing_time = (
                (self.stats.average_processing_time * (total - 1) + processing_time) / total
            )

    async def _get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the gateway."""
        return {
            "gateway": asdict(self.stats),
            "audio_processor": self.audio_processor.get_stats(),
            "intent_classifier": self.intent_classifier.get_stats(),
            "claude_interface": self.claude_interface.get_stats(),
            "uptime": time.time() - self.stats.uptime_start,
            "active_connections": list(self.active_connections.keys())
        }

    async def _heartbeat_task(self) -> None:
        """Background task to check connection health."""
        while self.running:
            try:
                current_time = time.time()
                stale_connections = []
                
                for connection_id, connection_info in self.active_connections.items():
                    # Check for stale connections (no activity for 5 minutes)
                    if current_time - connection_info.last_activity > 300:
                        stale_connections.append(connection_id)
                
                # Close stale connections
                for connection_id in stale_connections:
                    connection_info = self.active_connections.get(connection_id)
                    if connection_info:
                        logger.info(f"Closing stale connection: {connection_id}")
                        try:
                            await connection_info.websocket.close(code=1001, reason="Connection timeout")
                        except:
                            pass
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(5)

    async def _stats_logger_task(self) -> None:
        """Background task to periodically log statistics."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Log every 5 minutes
                
                stats = await self._get_comprehensive_stats()
                logger.info(f"Gateway Stats - Connections: {self.stats.active_connections}, "
                           f"Audio processed: {self.stats.total_audio_processed}, "
                           f"Claude commands: {self.stats.total_claude_commands}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stats logger task: {e}")

    async def run_forever(self) -> None:
        """Run the server indefinitely."""
        await self.start_server()
        try:
            # Keep the server running
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop_server()


# Main execution
async def main():
    """Main entry point for the Voice Gateway server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voice Gateway Server")
    parser.add_argument("--host", default="localhost", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind the server")
    parser.add_argument("--whisper-model", default="base", help="Whisper model to use")
    parser.add_argument("--claude-binary", default="claude", help="Path to Claude CLI binary")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run the gateway
    gateway = VoiceGateway(
        host=args.host,
        port=args.port,
        whisper_model=args.whisper_model,
        claude_binary=args.claude_binary
    )
    
    logger.info(f"Starting Voice Gateway with Whisper model: {args.whisper_model}")
    
    try:
        await gateway.run_forever()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
