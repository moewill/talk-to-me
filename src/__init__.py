"""
Voice-Driven Claude CLI Automation System

A complete system for processing voice commands and executing Claude CLI operations
through WebSocket connections with real-time audio processing.
"""

__version__ = "1.0.0"
__author__ = "Voice-Claude System"

# Import core components for easy access
from .audio_processor import AudioProcessor, TranscriptionResult
from .intent_classifier import IntentClassifier, IntentResult  
from .claude_interface import ClaudeInterface, ClaudeResponse
from .voice_gateway import VoiceGateway

# Export main classes
__all__ = [
    'AudioProcessor',
    'TranscriptionResult', 
    'IntentClassifier',
    'IntentResult',
    'ClaudeInterface', 
    'ClaudeResponse',
    'VoiceGateway'
]