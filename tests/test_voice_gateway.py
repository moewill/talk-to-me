"""
Comprehensive tests for the VoiceGateway module.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
import websockets
from src.voice_gateway import ConnectionInfo, ProcessingStats, VoiceGateway


@pytest.fixture
def voice_gateway():
    """Create a VoiceGateway instance for testing."""
    return VoiceGateway(host="localhost", port=8081, whisper_model="tiny", claude_binary="claude")


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = Mock()
    websocket.remote_address = ("127.0.0.1", 12345)
    websocket.send = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def mock_audio_data():
    """Create mock audio data for testing."""
    return b"mock_audio_data_16khz_pcm" * 100  # Some mock audio data


class TestVoiceGateway:
    """Test cases for VoiceGateway functionality."""
    
    def test_initialization(self, voice_gateway):
        """Test VoiceGateway initialization."""
        assert voice_gateway.host == "localhost"
        assert voice_gateway.port == 8081
        assert voice_gateway.max_connections == 10
        assert voice_gateway.connection_counter == 0
        assert len(voice_gateway.active_connections) == 0
        assert voice_gateway.running is False
        assert voice_gateway.server is None
        
        # Check components are initialized
        assert voice_gateway.audio_processor is not None
        assert voice_gateway.intent_classifier is not None
        assert voice_gateway.claude_interface is not None
        
        # Check stats initialization
        assert voice_gateway.stats.total_connections == 0
        assert voice_gateway.stats.active_connections == 0
        assert voice_gateway.stats.total_audio_processed == 0
    
    @pytest.mark.asyncio
    async def test_start_server_success(self, voice_gateway):
        """Test successful server startup."""
        with patch('websockets.serve') as mock_serve, \
             patch.object(voice_gateway.audio_processor, 'load_model') as mock_load_model, \
             patch.object(voice_gateway.claude_interface, 'test_connection') as mock_test_claude:
            
            mock_server = Mock()
            mock_serve.return_value = mock_server
            mock_load_model.return_value = True
            mock_test_claude.return_value = {'available': True}
            
            await voice_gateway.start_server()
            
            assert voice_gateway.running is True
            assert voice_gateway.server is mock_server
            mock_serve.assert_called_once()
            mock_load_model.assert_called_once()
            mock_test_claude.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_server_failure(self, voice_gateway):
        """Test server startup failure."""
        with patch('websockets.serve') as mock_serve:
            mock_serve.side_effect = Exception("Server startup failed")
            
            with pytest.raises(Exception, match="Server startup failed"):
                await voice_gateway.start_server()
            
            assert voice_gateway.running is False
            assert voice_gateway.server is None
    
    @pytest.mark.asyncio
    async def test_stop_server(self, voice_gateway):
        """Test server shutdown."""
        # Setup a running server
        mock_server = Mock()
        mock_server.close = Mock()
        mock_server.wait_closed = AsyncMock()
        voice_gateway.server = mock_server
        voice_gateway.running = True
        
        # Add a mock connection
        mock_websocket = Mock()
        mock_websocket.close = AsyncMock()
        connection_info = ConnectionInfo(
            websocket=mock_websocket,
            connection_id="test_conn",
            connected_at=time.time(),
            last_activity=time.time(),
            processed_messages=0
        )
        voice_gateway.active_connections["test_conn"] = connection_info
        
        await voice_gateway.stop_server()
        
        assert voice_gateway.running is False
        mock_server.close.assert_called_once()
        mock_server.wait_closed.assert_called_once()
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_connection_success(self, voice_gateway, mock_websocket):
        """Test successful connection handling."""
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway, '_process_messages') as mock_process:
            
            mock_send.return_value = None
            mock_process.return_value = None
            
            await voice_gateway.handle_connection(mock_websocket, "/")
            
            mock_send.assert_called_once()
            mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_connection_limit_exceeded(self, voice_gateway, mock_websocket):
        """Test connection limit enforcement."""
        # Fill up connections to the limit
        for i in range(voice_gateway.max_connections):
            voice_gateway.active_connections[f"conn_{i}"] = Mock()
        
        await voice_gateway.handle_connection(mock_websocket, "/")
        
        # Should close the connection due to limit
        mock_websocket.close.assert_called_once_with(code=1013, reason="Server overloaded")
    
    @pytest.mark.asyncio
    async def test_send_message(self, voice_gateway, mock_websocket):
        """Test sending JSON messages."""
        test_data = {"type": "test", "message": "hello"}
        
        await voice_gateway._send_message(mock_websocket, test_data)
        
        expected_message = json.dumps(test_data)
        mock_websocket.send.assert_called_once_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_send_error(self, voice_gateway, mock_websocket):
        """Test sending error messages."""
        error_message = "Test error"
        
        with patch.object(voice_gateway, '_send_message') as mock_send:
            await voice_gateway._send_error(mock_websocket, error_message)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args["type"] == "error"
            assert call_args["message"] == error_message
    
    @pytest.mark.asyncio
    async def test_handle_json_message_ping(self, voice_gateway, mock_websocket):
        """Test handling ping JSON messages."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        data = {"type": "ping"}
        
        with patch.object(voice_gateway, '_send_message') as mock_send:
            await voice_gateway._handle_json_message(connection_info, data)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args["type"] == "pong"
            assert "timestamp" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_json_message_get_stats(self, voice_gateway, mock_websocket):
        """Test handling get_stats JSON messages."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        data = {"type": "get_stats"}
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway, '_get_comprehensive_stats') as mock_stats:
            
            mock_stats.return_value = {"test": "stats"}
            
            await voice_gateway._handle_json_message(connection_info, data)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args["type"] == "stats"
            assert call_args["data"] == {"test": "stats"}
    
    @pytest.mark.asyncio
    async def test_handle_json_message_test_claude(self, voice_gateway, mock_websocket):
        """Test handling test_claude JSON messages."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        data = {"type": "test_claude"}
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway.claude_interface, 'test_connection') as mock_test:
            
            mock_test.return_value = {"available": True}
            
            await voice_gateway._handle_json_message(connection_info, data)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args["type"] == "claude_test"
            assert call_args["data"] == {"available": True}
    
    @pytest.mark.asyncio
    async def test_handle_json_message_text_command(self, voice_gateway, mock_websocket):
        """Test handling text_command JSON messages."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        data = {"type": "text_command", "text": "Claude write a function"}
        
        with patch.object(voice_gateway, '_process_text_command') as mock_process:
            await voice_gateway._handle_json_message(connection_info, data)
            
            mock_process.assert_called_once_with(connection_info, "Claude write a function")
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_success(self, voice_gateway, mock_websocket, mock_audio_data):
        """Test successful audio message handling."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        
        # Mock successful transcription
        mock_transcription = Mock()
        mock_transcription.success = True
        mock_transcription.text = "Claude write a function"
        mock_transcription.confidence = 0.9
        mock_transcription.language = "en"
        mock_transcription.processing_time = 1.5
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway.audio_processor, 'transcribe') as mock_transcribe, \
             patch.object(voice_gateway, '_process_text_command') as mock_process:
            
            mock_transcribe.return_value = mock_transcription
            
            await voice_gateway._handle_audio_message(connection_info, mock_audio_data)
            
            # Should send processing acknowledgment and transcription result
            assert mock_send.call_count >= 2
            mock_transcribe.assert_called_once_with(mock_audio_data)
            mock_process.assert_called_once_with(connection_info, "Claude write a function")
            
            # Check stats were updated
            assert voice_gateway.stats.total_audio_processed == 1
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_transcription_failure(self, voice_gateway, mock_websocket, mock_audio_data):
        """Test audio message handling with transcription failure."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        
        # Mock failed transcription
        mock_transcription = Mock()
        mock_transcription.success = False
        mock_transcription.error = "Transcription failed"
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway, '_send_error') as mock_send_error, \
             patch.object(voice_gateway.audio_processor, 'transcribe') as mock_transcribe:
            
            mock_transcribe.return_value = mock_transcription
            
            await voice_gateway._handle_audio_message(connection_info, mock_audio_data)
            
            mock_send_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_text_command_claude_detection(self, voice_gateway, mock_websocket):
        """Test text command processing with Claude command detection."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        text = "Claude write a function"
        
        # Mock intent classification
        mock_intent = Mock()
        mock_intent.is_claude_command = True
        mock_intent.command = "write a function"
        mock_intent.confidence = 0.9
        mock_intent.detected_keywords = ["claude"]
        mock_intent.original_text = text
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway.intent_classifier, 'detect_intent') as mock_detect, \
             patch.object(voice_gateway, '_execute_claude_command') as mock_execute:
            
            mock_detect.return_value = mock_intent
            
            await voice_gateway._process_text_command(connection_info, text)
            
            mock_detect.assert_called_once_with(text)
            mock_execute.assert_called_once_with(connection_info, "write a function")
            
            # Should send intent classification result
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args["type"] == "intent"
            assert call_args["is_claude_command"] is True
    
    @pytest.mark.asyncio
    async def test_process_text_command_no_claude_detection(self, voice_gateway, mock_websocket):
        """Test text command processing without Claude command detection."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        text = "Just regular conversation"
        
        # Mock intent classification
        mock_intent = Mock()
        mock_intent.is_claude_command = False
        mock_intent.command = ""
        mock_intent.confidence = 0.1
        mock_intent.detected_keywords = []
        mock_intent.original_text = text
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway.intent_classifier, 'detect_intent') as mock_detect, \
             patch.object(voice_gateway, '_execute_claude_command') as mock_execute:
            
            mock_detect.return_value = mock_intent
            
            await voice_gateway._process_text_command(connection_info, text)
            
            mock_detect.assert_called_once_with(text)
            mock_execute.assert_not_called()  # Should not execute Claude command
            
            # Should send intent classification result
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args["type"] == "intent"
            assert call_args["is_claude_command"] is False
    
    @pytest.mark.asyncio
    async def test_execute_claude_command_success(self, voice_gateway, mock_websocket):
        """Test successful Claude command execution."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        command = "write a function"
        
        # Mock successful Claude response
        mock_response = Mock()
        mock_response.success = True
        mock_response.output = "def hello_world():\n    print('Hello, World!')"
        mock_response.error = ""
        mock_response.execution_time = 2.5
        mock_response.command = command
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway.claude_interface, 'execute_command') as mock_execute:
            
            mock_execute.return_value = mock_response
            
            await voice_gateway._execute_claude_command(connection_info, command)
            
            mock_execute.assert_called_once_with(command)
            
            # Should send execution start and result messages
            assert mock_send.call_count == 2
            
            # Check stats were updated
            assert voice_gateway.stats.total_claude_commands == 1
            assert voice_gateway.stats.successful_claude_commands == 1
    
    @pytest.mark.asyncio
    async def test_execute_claude_command_failure(self, voice_gateway, mock_websocket):
        """Test Claude command execution failure."""
        connection_info = Mock()
        connection_info.websocket = mock_websocket
        command = "invalid command"
        
        # Mock failed Claude response
        mock_response = Mock()
        mock_response.success = False
        mock_response.output = ""
        mock_response.error = "Command execution failed"
        mock_response.execution_time = 1.0
        mock_response.command = command
        
        with patch.object(voice_gateway, '_send_message') as mock_send, \
             patch.object(voice_gateway.claude_interface, 'execute_command') as mock_execute:
            
            mock_execute.return_value = mock_response
            
            await voice_gateway._execute_claude_command(connection_info, command)
            
            mock_execute.assert_called_once_with(command)
            
            # Should send execution start and result messages
            assert mock_send.call_count == 2
            
            # Check stats were updated
            assert voice_gateway.stats.total_claude_commands == 1
            assert voice_gateway.stats.successful_claude_commands == 0
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_stats(self, voice_gateway):
        """Test comprehensive statistics retrieval."""
        # Mock component stats
        with patch.object(voice_gateway.audio_processor, 'get_stats') as mock_audio_stats, \
             patch.object(voice_gateway.intent_classifier, 'get_stats') as mock_intent_stats, \
             patch.object(voice_gateway.claude_interface, 'get_stats') as mock_claude_stats:
            
            mock_audio_stats.return_value = {"audio": "stats"}
            mock_intent_stats.return_value = {"intent": "stats"}
            mock_claude_stats.return_value = {"claude": "stats"}
            
            stats = await voice_gateway._get_comprehensive_stats()
            
            assert "gateway" in stats
            assert "audio_processor" in stats
            assert "intent_classifier" in stats
            assert "claude_interface" in stats
            assert "uptime" in stats
            assert "active_connections" in stats
    
    def test_update_processing_time(self, voice_gateway):
        """Test processing time statistics update."""
        # First update
        voice_gateway._update_processing_time(2.0)
        assert voice_gateway.stats.average_processing_time == 2.0
        
        # Second update should calculate average
        voice_gateway.stats.total_audio_processed = 2
        voice_gateway._update_processing_time(4.0)
        assert voice_gateway.stats.average_processing_time == 3.0
    
    @pytest.mark.asyncio
    async def test_heartbeat_task_removes_stale_connections(self, voice_gateway):
        """Test that heartbeat task removes stale connections."""
        # Add a stale connection
        mock_websocket = Mock()
        mock_websocket.close = AsyncMock()
        
        stale_connection = ConnectionInfo(
            websocket=mock_websocket,
            connection_id="stale_conn",
            connected_at=time.time() - 400,  # 400 seconds ago
            last_activity=time.time() - 400,  # 400 seconds ago
            processed_messages=0
        )
        voice_gateway.active_connections["stale_conn"] = stale_connection
        voice_gateway.running = True
        
        # Run one iteration of heartbeat task
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError()]  # Stop after one iteration
            
            try:
                await voice_gateway._heartbeat_task()
            except asyncio.CancelledError:
                pass
            
            # Stale connection should be closed
            mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stats_logger_task(self, voice_gateway):
        """Test stats logger background task."""
        voice_gateway.running = True
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(voice_gateway, '_get_comprehensive_stats') as mock_stats:
            
            mock_sleep.side_effect = [None, asyncio.CancelledError()]  # Stop after one iteration
            mock_stats.return_value = {"test": "stats"}
            
            try:
                await voice_gateway._stats_logger_task()
            except asyncio.CancelledError:
                pass
            
            mock_stats.assert_called_once()
    
    def test_connection_info_dataclass(self):
        """Test ConnectionInfo dataclass functionality."""
        mock_websocket = Mock()
        connection_info = ConnectionInfo(
            websocket=mock_websocket,
            connection_id="test_conn",
            connected_at=1234567890.0,
            last_activity=1234567890.0,
            processed_messages=5
        )
        
        assert connection_info.websocket is mock_websocket
        assert connection_info.connection_id == "test_conn"
        assert connection_info.connected_at == 1234567890.0
        assert connection_info.last_activity == 1234567890.0
        assert connection_info.processed_messages == 5
    
    def test_processing_stats_dataclass(self):
        """Test ProcessingStats dataclass functionality."""
        stats = ProcessingStats(
            total_connections=10,
            active_connections=5,
            total_audio_processed=100,
            total_claude_commands=50,
            successful_claude_commands=45,
            average_processing_time=2.5,
            uptime_start=1234567890.0
        )
        
        assert stats.total_connections == 10
        assert stats.active_connections == 5
        assert stats.total_audio_processed == 100
        assert stats.total_claude_commands == 50
        assert stats.successful_claude_commands == 45
        assert stats.average_processing_time == 2.5
        assert stats.uptime_start == 1234567890.0
    
    @pytest.mark.asyncio
    async def test_run_forever_keyboard_interrupt(self, voice_gateway):
        """Test run_forever method with keyboard interrupt."""
        with patch.object(voice_gateway, 'start_server') as mock_start, \
             patch.object(voice_gateway, 'stop_server') as mock_stop:
            
            mock_start.return_value = None
            
            # Simulate keyboard interrupt after start
            async def interrupt_after_start():
                raise KeyboardInterrupt()
            
            with patch('asyncio.Future') as mock_future:
                mock_future.side_effect = interrupt_after_start
                
                await voice_gateway.run_forever()
                
                mock_start.assert_called_once()
                mock_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_edge_cases_empty_message_handling(self, voice_gateway):
        """Test handling of various edge cases in message processing."""
        connection_info = Mock()
        connection_info.websocket = Mock()
        connection_info.last_activity = time.time()
        connection_info.processed_messages = 0
        
        # Test empty JSON message
        with patch.object(voice_gateway, '_handle_json_message') as mock_handle_json:
            with patch.object(voice_gateway, '_send_error') as mock_send_error:
                try:
                    await voice_gateway._process_messages(connection_info)
                except StopAsyncIteration:
                    pass  # Expected when mocking async iterator
    
    def test_configuration_parameters(self):
        """Test various configuration parameters."""
        gateway = VoiceGateway(
            host="192.168.1.100",
            port=9090,
            whisper_model="medium",
            claude_binary="/usr/local/bin/claude"
        )
        
        assert gateway.host == "192.168.1.100"
        assert gateway.port == 9090
        assert gateway.audio_processor.model_name == "medium"
        assert gateway.claude_interface.claude_binary == "/usr/local/bin/claude"
