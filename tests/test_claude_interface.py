"""
Comprehensive tests for the ClaudeInterface module.
"""

import asyncio
import subprocess
from unittest.mock import AsyncMock, Mock, patch

import pytest
from src.claude_interface import ClaudeInterface, ClaudeResponse


@pytest.fixture
def claude_interface():
    """Create a ClaudeInterface instance for testing."""
    return ClaudeInterface(claude_binary="claude")


@pytest.fixture
def mock_subprocess_success():
    """Create a mock subprocess that returns successful results."""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = "Successfully executed command\nOutput here"
    mock_process.stderr = ""
    return mock_process


@pytest.fixture
def mock_subprocess_failure():
    """Create a mock subprocess that returns failure results."""
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stdout = ""
    mock_process.stderr = "Error: Command failed"
    return mock_process


class TestClaudeInterface:
    """Test cases for ClaudeInterface functionality."""
    
    def test_initialization(self, claude_interface):
        """Test ClaudeInterface initialization."""
        assert claude_interface.claude_binary == "claude"
        assert claude_interface.timeout == 30
        assert claude_interface.stats.total_commands == 0
        assert claude_interface.stats.successful_commands == 0
        assert claude_interface.stats.failed_commands == 0
        assert len(claude_interface.command_history) == 0
    
    def test_initialization_custom_params(self):
        """Test ClaudeInterface initialization with custom parameters."""
        interface = ClaudeInterface(claude_binary="/usr/local/bin/claude", timeout=60)
        assert interface.claude_binary == "/usr/local/bin/claude"
        assert interface.timeout == 60
    
    @pytest.mark.asyncio
    async def test_check_claude_availability_success(self, claude_interface):
        """Test successful Claude availability check."""
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_process = Mock()
            mock_process.wait.return_value = asyncio.Future()
            mock_process.wait.return_value.set_result(0)
            mock_process.stdout.read.return_value = asyncio.Future()
            mock_process.stdout.read.return_value.set_result(b"Claude CLI v1.0")
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_process)
            
            result = await claude_interface._check_claude_availability()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_claude_availability_failure(self, claude_interface):
        """Test Claude availability check when Claude is not available."""
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_create.side_effect = FileNotFoundError("Command not found")
            
            result = await claude_interface._check_claude_availability()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, claude_interface):
        """Test successful connection test."""
        with patch.object(claude_interface, '_check_claude_availability') as mock_check:
            mock_check.return_value = True
            
            result = await claude_interface.test_connection()
            
            assert result['available'] is True
            assert result['binary_path'] == "claude"
            assert 'tested_at' in result
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, claude_interface):
        """Test connection test when Claude is not available."""
        with patch.object(claude_interface, '_check_claude_availability') as mock_check:
            mock_check.return_value = False
            
            result = await claude_interface.test_connection()
            
            assert result['available'] is False
            assert result['binary_path'] == "claude"
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_execute_command_success(self, claude_interface, mock_subprocess_success):
        """Test successful command execution."""
        command = "write a hello world function"
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_subprocess_success)
            
            result = await claude_interface.execute_command(command)
            
            assert isinstance(result, ClaudeResponse)
            assert result.success is True
            assert "Successfully executed command" in result.output
            assert result.error == ""
            assert result.command == command
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_command_failure(self, claude_interface, mock_subprocess_failure):
        """Test command execution failure."""
        command = "invalid command"
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_subprocess_failure)
            
            result = await claude_interface.execute_command(command)
            
            assert isinstance(result, ClaudeResponse)
            assert result.success is False
            assert result.output == ""
            assert "Error: Command failed" in result.error
            assert result.command == command
    
    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, claude_interface):
        """Test command execution timeout."""
        command = "long running command"
        claude_interface.timeout = 0.1  # Very short timeout
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            # Create a process that never completes
            mock_process = Mock()
            mock_process.wait.return_value = asyncio.Future()  # Never completes
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_process)
            
            result = await claude_interface.execute_command(command)
            
            assert isinstance(result, ClaudeResponse)
            assert result.success is False
            assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_command_empty_command(self, claude_interface):
        """Test execution with empty command."""
        result = await claude_interface.execute_command("")
        
        assert isinstance(result, ClaudeResponse)
        assert result.success is False
        assert "empty command" in result.error.lower()
        assert result.command == ""
    
    @pytest.mark.asyncio
    async def test_execute_command_whitespace_only(self, claude_interface):
        """Test execution with whitespace-only command."""
        result = await claude_interface.execute_command("   \t\n  ")
        
        assert isinstance(result, ClaudeResponse)
        assert result.success is False
        assert "empty command" in result.error.lower()
    
    def test_prepare_command_basic(self, claude_interface):
        """Test basic command preparation."""
        command = "write a function"
        prepared = claude_interface._prepare_command(command)
        
        assert isinstance(prepared, list)
        assert "claude" in prepared[0]
        assert command in " ".join(prepared)
    
    def test_prepare_command_with_quotes(self, claude_interface):
        """Test command preparation with quotes."""
        command = 'write a function called "hello_world"'
        prepared = claude_interface._prepare_command(command)
        
        assert isinstance(prepared, list)
        assert len(prepared) >= 2
    
    def test_prepare_command_multiline(self, claude_interface):
        """Test command preparation with multiline input."""
        command = """write a function that:
        1. Takes a number as input
        2. Returns the square of that number"""
        
        prepared = claude_interface._prepare_command(command)
        
        assert isinstance(prepared, list)
        assert len(prepared) >= 2
    
    def test_clean_output_ansi_codes(self, claude_interface):
        """Test cleaning of ANSI color codes from output."""
        output_with_ansi = "\033[31mError:\033[0m Something went wrong\033[32m Success\033[0m"
        cleaned = claude_interface._clean_output(output_with_ansi)
        
        assert "\033[" not in cleaned
        assert "Error: Something went wrong Success" in cleaned
    
    def test_clean_output_control_characters(self, claude_interface):
        """Test cleaning of control characters from output."""
        output_with_control = "Hello\r\nWorld\x08\x1b[KTest"
        cleaned = claude_interface._clean_output(output_with_control)
        
        # Should remove or normalize control characters
        assert len(cleaned) <= len(output_with_control)
        assert "Hello" in cleaned
        assert "World" in cleaned
        assert "Test" in cleaned
    
    def test_clean_output_empty(self, claude_interface):
        """Test cleaning of empty output."""
        assert claude_interface._clean_output("") == ""
        assert claude_interface._clean_output(None) == ""
    
    def test_validate_command_valid(self, claude_interface):
        """Test validation of valid commands."""
        valid_commands = [
            "write a function",
            "help me debug this code",
            "explain this algorithm",
            "create a new file with content"
        ]
        
        for command in valid_commands:
            assert claude_interface._validate_command(command) is True
    
    def test_validate_command_invalid(self, claude_interface):
        """Test validation of invalid commands."""
        invalid_commands = [
            "",
            "   ",
            "\t\n",
            None
        ]
        
        for command in invalid_commands:
            assert claude_interface._validate_command(command) is False
    
    def test_get_stats(self, claude_interface):
        """Test statistics retrieval."""
        # Manually update some stats
        claude_interface.stats.total_commands = 10
        claude_interface.stats.successful_commands = 8
        claude_interface.stats.failed_commands = 2
        claude_interface.stats.total_execution_time = 50.0
        
        stats = claude_interface.get_stats()
        
        assert stats['total_commands'] == 10
        assert stats['successful_commands'] == 8
        assert stats['failed_commands'] == 2
        assert stats['success_rate'] == 0.8
        assert stats['average_execution_time'] == 5.0
        assert 'total_execution_time' in stats
    
    def test_get_stats_no_commands(self, claude_interface):
        """Test statistics when no commands have been executed."""
        stats = claude_interface.get_stats()
        
        assert stats['total_commands'] == 0
        assert stats['successful_commands'] == 0
        assert stats['failed_commands'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_execution_time'] == 0.0
    
    @pytest.mark.asyncio
    async def test_execute_command_updates_stats(self, claude_interface, mock_subprocess_success):
        """Test that command execution updates statistics."""
        command = "test command"
        initial_count = claude_interface.stats.total_commands
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_subprocess_success)
            
            await claude_interface.execute_command(command)
            
            assert claude_interface.stats.total_commands == initial_count + 1
            assert claude_interface.stats.successful_commands == 1
            assert claude_interface.stats.total_execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_command_updates_history(self, claude_interface, mock_subprocess_success):
        """Test that command execution updates command history."""
        command = "test command"
        initial_history_length = len(claude_interface.command_history)
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_subprocess_success)
            
            result = await claude_interface.execute_command(command)
            
            assert len(claude_interface.command_history) == initial_history_length + 1
            assert claude_interface.command_history[-1].command == command
            assert claude_interface.command_history[-1].success == result.success
    
    def test_command_history_limit(self, claude_interface):
        """Test that command history respects the maximum limit."""
        # Manually add commands to exceed the limit
        for i in range(claude_interface.max_history_size + 10):
            claude_interface.command_history.append(
                ClaudeResponse(
                    success=True,
                    output=f"Output {i}",
                    error="",
                    command=f"Command {i}",
                    execution_time=1.0
                )
            )
        
        assert len(claude_interface.command_history) == claude_interface.max_history_size
    
    @pytest.mark.asyncio
    async def test_concurrent_command_execution(self, claude_interface):
        """Test concurrent command execution."""
        commands = ["command 1", "command 2", "command 3"]
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Success"
            mock_process.stderr = ""
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_process)
            
            # Execute commands concurrently
            tasks = [claude_interface.execute_command(cmd) for cmd in commands]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            for result in results:
                assert isinstance(result, ClaudeResponse)
                assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execute_command_subprocess_error(self, claude_interface):
        """Test handling of subprocess creation errors."""
        command = "test command"
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_create.side_effect = OSError("Subprocess creation failed")
            
            result = await claude_interface.execute_command(command)
            
            assert isinstance(result, ClaudeResponse)
            assert result.success is False
            assert "subprocess creation failed" in result.error.lower()
    
    def test_edge_cases_command_types(self, claude_interface):
        """Test various edge cases for command types."""
        edge_cases = [
            123,     # Integer
            [],      # List
            {},      # Dictionary
            True,    # Boolean
        ]
        
        for case in edge_cases:
            try:
                result = claude_interface._validate_command(case)
                assert result is False
            except (TypeError, AttributeError):
                # It's acceptable to raise an exception for invalid input types
                pass
    
    @pytest.mark.asyncio
    async def test_large_output_handling(self, claude_interface):
        """Test handling of large command outputs."""
        command = "generate large output"
        large_output = "A" * 10000  # 10KB output
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = large_output
            mock_process.stderr = ""
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_process)
            
            result = await claude_interface.execute_command(command)
            
            assert isinstance(result, ClaudeResponse)
            assert result.success is True
            assert len(result.output) == 10000
    
    @pytest.mark.asyncio
    async def test_special_characters_in_command(self, claude_interface):
        """Test handling of special characters in commands."""
        commands_with_special_chars = [
            "write a function with $pecial characters",
            "handle unicode: café, naïve, résumé",
            "process symbols: !@#$%^&*()",
            "newlines and\ttabs\nhere"
        ]
        
        with patch('asyncio.subprocess.create_subprocess_exec') as mock_create:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Success"
            mock_process.stderr = ""
            mock_create.return_value = asyncio.Future()
            mock_create.return_value.set_result(mock_process)
            
            for command in commands_with_special_chars:
                result = await claude_interface.execute_command(command)
                assert isinstance(result, ClaudeResponse)
                # Should handle special characters gracefully
