"""
Claude CLI Interface for Voice-driven automation system.

This module provides an asynchronous interface to execute Claude CLI commands
via subprocess, with proper error handling, response processing, and execution
history tracking.
"""

import asyncio
import json
import logging
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """Response from Claude CLI execution."""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    timestamp: float
    command: str
    raw_output: str


@dataclass
class ClaudeStats:
    """Statistics for Claude CLI usage."""
    total_commands: int
    successful_commands: int
    failed_commands: int
    average_execution_time: float
    last_execution: Optional[float]


class ClaudeInterface:
    """
    Asynchronous interface to Claude CLI.
    
    Handles command execution, response processing, error handling,
    and maintains execution history for debugging and monitoring.
    """
    
    def __init__(self, claude_binary: str = "claude", timeout: int = 30):
        """
        Initialize Claude CLI interface.
        
        Args:
            claude_binary: Path or name of the Claude CLI binary
            timeout: Maximum execution time in seconds
        """
        self.claude_binary = claude_binary
        self.timeout = timeout
        self.execution_history: List[ClaudeResponse] = []
        self.max_history = 100  # Keep last 100 executions
        
        # Statistics tracking
        self._stats = ClaudeStats(
            total_commands=0,
            successful_commands=0,
            failed_commands=0,
            average_execution_time=0.0,
            last_execution=None
        )
        
        # Validate Claude CLI availability
        self._claude_available = None

    async def execute_command(
        self, 
        command: str, 
        model: str = None,  # Use default model
        additional_args: Optional[List[str]] = None
    ) -> ClaudeResponse:
        """
        Execute a command using Claude CLI.
        
        Args:
            command: The prompt/command to send to Claude
            model: Claude model to use
            additional_args: Additional CLI arguments
            
        Returns:
            ClaudeResponse with execution results
        """
        start_time = time.time()
        
        try:
            # Check if Claude CLI is available
            if not await self._check_claude_availability():
                return ClaudeResponse(
                    success=False,
                    output="",
                    error="Claude CLI not found or not accessible",
                    exit_code=-1,
                    execution_time=0.0,
                    timestamp=start_time,
                    command=command,
                    raw_output=""
                )
            
            # Prepare the CLI command
            cli_command = await self._prepare_command(command, model, additional_args)
            
            # Execute the command
            result = await self._run_command(cli_command, command)
            
            # Update statistics
            self._update_stats(result)
            
            # Add to history
            self._add_to_history(result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ClaudeResponse(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                timestamp=start_time,
                command=command,
                raw_output=""
            )
            
            self._update_stats(error_result)
            self._add_to_history(error_result)
            
            logger.error(f"Claude execution error: {e}")
            return error_result

    async def _check_claude_availability(self) -> bool:
        """Check if Claude CLI is available and accessible."""
        if self._claude_available is not None:
            return self._claude_available
        
        try:
            # Try to run Claude with --version or --help
            process = await asyncio.create_subprocess_exec(
                self.claude_binary, '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=5.0
            )
            
            self._claude_available = process.returncode == 0
            
            if self._claude_available:
                version_info = stdout.decode().strip() or stderr.decode().strip()
                logger.info(f"Claude CLI available: {version_info}")
            else:
                logger.warning("Claude CLI not responding correctly")
                
        except (asyncio.TimeoutError, FileNotFoundError, OSError) as e:
            logger.warning(f"Claude CLI not found: {e}")
            self._claude_available = False
        
        return self._claude_available

    async def _prepare_command(
        self, 
        command: str, 
        model: str, 
        additional_args: Optional[List[str]]
    ) -> List[str]:
        """Prepare the CLI command arguments."""
        # Base command
        cli_args = [self.claude_binary]
        
        # Add model if specified (otherwise use default)
        if model:
            cli_args.extend(['--model', model])
        
        # Add additional arguments
        if additional_args:
            cli_args.extend(additional_args)
        
        # Add the prompt/command
        cli_args.append(command)
        
        return cli_args

    async def _run_command(self, cli_command: List[str], original_command: str) -> ClaudeResponse:
        """Execute the prepared CLI command."""
        start_time = time.time()
        
        try:
            # Use regular subprocess.run in a thread for better compatibility
            loop = asyncio.get_event_loop()
            
            def run_claude_sync():
                return subprocess.run(
                    cli_command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            
            # Run in thread to avoid blocking
            result = await loop.run_in_executor(None, run_claude_sync)
            
            execution_time = time.time() - start_time
            
            # Get outputs from result
            stdout_text = result.stdout or ""
            stderr_text = result.stderr or ""
            
            # Process the response
            processed_output = self._process_output(stdout_text, stderr_text)
            
            return ClaudeResponse(
                success=result.returncode == 0,
                output=processed_output,
                error=stderr_text if result.returncode != 0 else "",
                exit_code=result.returncode,
                execution_time=execution_time,
                timestamp=start_time,
                command=original_command,
                raw_output=stdout_text
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Command timed out after {self.timeout} seconds",
                exit_code=-1,
                execution_time=execution_time,
                timestamp=start_time,
                command=original_command,
                raw_output=""
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Subprocess error: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                timestamp=start_time,
                command=original_command,
                raw_output=""
            )

    def _process_output(self, stdout: str, stderr: str) -> str:
        """Process and clean the output from Claude CLI."""
        if not stdout and not stderr:
            return ""
        
        # If there's stdout, use it as primary output
        if stdout.strip():
            # Clean up common CLI artifacts
            output = stdout.strip()
            
            # Remove ANSI color codes if present
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            output = ansi_escape.sub('', output)
            
            return output
        
        # Fallback to stderr if no stdout
        return stderr.strip()

    def _update_stats(self, result: ClaudeResponse) -> None:
        """Update execution statistics."""
        self._stats.total_commands += 1
        
        if result.success:
            self._stats.successful_commands += 1
        else:
            self._stats.failed_commands += 1
        
        # Update average execution time
        if self._stats.total_commands == 1:
            self._stats.average_execution_time = result.execution_time
        else:
            # Running average
            self._stats.average_execution_time = (
                (self._stats.average_execution_time * (self._stats.total_commands - 1) + 
                 result.execution_time) / self._stats.total_commands
            )
        
        self._stats.last_execution = result.timestamp

    def _add_to_history(self, result: ClaudeResponse) -> None:
        """Add execution result to history."""
        self.execution_history.append(result)
        
        # Trim history if it gets too long
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        stats_dict = asdict(self._stats)
        
        # Add success rate
        if self._stats.total_commands > 0:
            stats_dict['success_rate'] = (
                self._stats.successful_commands / self._stats.total_commands
            )
        else:
            stats_dict['success_rate'] = 0.0
        
        # Add recent performance
        recent_results = self.execution_history[-10:]  # Last 10 executions
        if recent_results:
            recent_success_count = sum(1 for r in recent_results if r.success)
            stats_dict['recent_success_rate'] = recent_success_count / len(recent_results)
            stats_dict['recent_avg_time'] = sum(r.execution_time for r in recent_results) / len(recent_results)
        else:
            stats_dict['recent_success_rate'] = 0.0
            stats_dict['recent_avg_time'] = 0.0
        
        return stats_dict

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get execution history."""
        history = self.execution_history
        if limit:
            history = history[-limit:]
        
        return [asdict(result) for result in history]

    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()
        logger.info("Execution history cleared")

    async def validate_response(self, response: ClaudeResponse) -> bool:
        """Validate if a Claude response is meaningful."""
        if not response.success:
            return False
        
        if not response.output or len(response.output.strip()) < 5:
            return False
        
        # Check for common error patterns in output
        error_indicators = [
            'error:', 'failed:', 'exception:', 'traceback:',
            'command not found', 'permission denied'
        ]
        
        output_lower = response.output.lower()
        for indicator in error_indicators:
            if indicator in output_lower:
                return False
        
        return True

    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Claude CLI."""
        test_command = "Hello, please respond with 'Connection test successful'"
        
        result = await self.execute_command(test_command)
        
        return {
            'available': await self._check_claude_availability(),
            'test_successful': result.success,
            'response': result.output if result.success else result.error,
            'execution_time': result.execution_time
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_claude_interface():
        """Test the Claude interface functionality."""
        interface = ClaudeInterface()
        
        print("Testing Claude CLI Interface...")
        print("=" * 40)
        
        # Test connection
        connection_test = await interface.test_connection()
        print(f"Connection Test: {connection_test}")
        print()
        
        if not connection_test['available']:
            print("Claude CLI not available. Ending test.")
            return
        
        # Test commands
        test_commands = [
            "What is 2 + 2?",
            "Write a simple hello world function in Python",
            "Explain what machine learning is in one sentence"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"Test {i}: {command}")
            
            result = await interface.execute_command(command)
            
            print(f"Success: {result.success}")
            print(f"Execution Time: {result.execution_time:.2f}s")
            
            if result.success:
                print(f"Output: {result.output[:200]}...")
            else:
                print(f"Error: {result.error}")
            
            print("-" * 40)
        
        # Print statistics
        stats = interface.get_stats()
        print(f"Statistics: {stats}")
    
    # Run the test
    asyncio.run(test_claude_interface())
