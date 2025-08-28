"""
Intent Classifier for Voice-driven Claude CLI automation system.

This module handles detecting Claude commands from voice transcriptions using
an LLM to understand natural language intent. Provides intelligent command
detection and extraction without requiring specific keyword patterns.
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of intent classification."""
    is_claude_command: bool
    command: Optional[str]
    confidence: float
    original_text: str
    detected_keywords: List[str]


class IntentClassifier:
    """
    Classifies voice transcriptions to detect Claude commands using LLM reasoning.
    
    Uses Claude CLI to intelligently determine if transcribed speech represents
    a request that should be forwarded to Claude for processing. This allows for
    natural language understanding without hardcoded patterns.
    """
    
    def __init__(self, claude_binary: str = "claude"):
        """Initialize the LLM-based intent classifier."""
        self.claude_binary = claude_binary
        self.stats = {
            'total_classifications': 0,
            'claude_commands_detected': 0,
            'classification_failures': 0,
            'average_response_time': 0.0
        }
        
        # Test Claude availability
        self.claude_available = self._test_claude_availability()
        
        if not self.claude_available:
            logger.warning("Claude CLI not available - will use fallback classification")
    
    def _test_claude_availability(self) -> bool:
        """Test if Claude CLI is available."""
        try:
            result = subprocess.run(
                [self.claude_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def detect_intent(self, text: str) -> IntentResult:
        """
        Detect if the given text contains a Claude command using LLM reasoning.
        
        Args:
            text: The transcribed voice text to analyze
            
        Returns:
            IntentResult with classification details and extracted command
        """
        start_time = asyncio.get_event_loop().time()
        
        if not text or not text.strip():
            return IntentResult(
                is_claude_command=False,
                command=None,
                confidence=0.0,
                original_text=text,
                detected_keywords=[]
            )
        
        # Clean text
        cleaned_text = text.strip()
        
        # Quick filters for obvious non-commands
        if self._is_obviously_not_command(cleaned_text):
            return IntentResult(
                is_claude_command=False,
                command=None,
                confidence=0.0,
                original_text=text,
                detected_keywords=[]
            )
        
        try:
            # Use LLM to classify intent
            if self.claude_available:
                result = self._classify_with_llm(cleaned_text)
            else:
                result = self._classify_with_fallback(cleaned_text)
            
            # Update stats
            self.stats['total_classifications'] += 1
            if result.is_claude_command:
                self.stats['claude_commands_detected'] += 1
            
            processing_time = asyncio.get_event_loop().time() - start_time
            self._update_avg_response_time(processing_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            self.stats['classification_failures'] += 1
            
            # Return safe fallback
            return IntentResult(
                is_claude_command=False,
                command=None,
                confidence=0.0,
                original_text=text,
                detected_keywords=['error']
            )

    def _is_obviously_not_command(self, text: str) -> bool:
        """Quick filter for obviously non-command text."""
        text_lower = text.lower().strip()
        
        # Single words that are clearly not commands
        non_commands = {'um', 'uh', 'er', 'ah', 'hmm', 'okay', 'ok', 'yes', 'no', 'start'}
        if text_lower in non_commands:
            return True
            
        # Very short or empty
        if len(text_lower) < 3:
            return True
            
        return False
    
    def _classify_with_llm(self, text: str) -> IntentResult:
        """Use Claude LLM to classify intent."""
        prompt = f"""You are analyzing speech transcripts from a voice assistant interface. 
Your job is to determine if the user's speech represents a request that should be forwarded to Claude AI for processing.

Analyze this transcribed speech: "{text}"

Consider these as Claude commands:
- Questions asking for information (what, how, where, when, who, why)
- Requests for explanations, help, or assistance  
- Commands to perform actions (list, show, tell, explain, create, etc.)
- Casual requests like "tell me a joke" or "help me with this"
- Any request that sounds like the user wants an AI assistant to respond

Consider these as NOT Claude commands:
- Single words like "start", "stop", "yes", "no"
- Speech artifacts like "um", "uh", "er"  
- Incomplete fragments
- Ambient speech not directed at the assistant

Respond with ONLY a JSON object in this exact format:
{{"is_command": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation", "command_text": "cleaned version of the command or null"}}"""

        try:
            result = subprocess.run(
                [self.claude_binary, "--print"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Claude CLI error: {result.stderr}")
                return self._classify_with_fallback(text)
            
            # Parse JSON response (handle markdown code blocks)
            raw_output = result.stdout.strip()
            
            # Extract JSON from markdown code blocks if present
            if raw_output.startswith('```json'):
                # Extract content between ```json and ```
                json_start = raw_output.find('```json') + 7
                json_end = raw_output.find('```', json_start)
                if json_end != -1:
                    json_content = raw_output[json_start:json_end].strip()
                else:
                    json_content = raw_output[json_start:].strip()
            elif raw_output.startswith('```'):
                # Handle generic code blocks
                json_start = raw_output.find('```') + 3
                json_end = raw_output.find('```', json_start)
                if json_end != -1:
                    json_content = raw_output[json_start:json_end].strip()
                else:
                    json_content = raw_output[json_start:].strip()
            else:
                json_content = raw_output
            
            response = json.loads(json_content)
            
            return IntentResult(
                is_claude_command=response.get('is_command', False),
                command=response.get('command_text') or (text if response.get('is_command', False) else None),
                confidence=float(response.get('confidence', 0.0)),
                original_text=text,
                detected_keywords=['llm_classified']
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Raw response: {result.stdout}")
            return self._classify_with_fallback(text)
        except Exception as e:
            logger.error(f"Claude LLM classification failed: {e}")
            return self._classify_with_fallback(text)
    
    def _classify_with_fallback(self, text: str) -> IntentResult:
        """Fallback classification when LLM is unavailable."""
        # Simple heuristic-based classification
        text_lower = text.lower()
        
        # Command indicators
        command_indicators = [
            'what', 'how', 'where', 'when', 'who', 'why',
            'tell me', 'show me', 'help me', 'explain', 
            'list', 'display', 'get', 'find'
        ]
        
        has_indicator = any(indicator in text_lower for indicator in command_indicators)
        is_question = text.strip().endswith('?') or text_lower.startswith(('what', 'how', 'where', 'when', 'who', 'why'))
        
        if has_indicator or is_question:
            return IntentResult(
                is_claude_command=True,
                command=text,
                confidence=0.7,
                original_text=text,
                detected_keywords=['fallback_heuristic']
            )
        
        return IntentResult(
            is_claude_command=False,
            command=None,
            confidence=0.1,
            original_text=text,
            detected_keywords=['fallback_negative']
        )

    def _update_avg_response_time(self, response_time: float) -> None:
        """Update average response time statistics."""
        if self.stats['total_classifications'] == 1:
            self.stats['average_response_time'] = response_time
        else:
            total = self.stats['total_classifications']
            current_avg = self.stats['average_response_time']
            self.stats['average_response_time'] = (current_avg * (total - 1) + response_time) / total
    
    def get_stats(self) -> Dict[str, any]:
        """Get classification statistics."""
        stats = self.stats.copy()
        if stats['total_classifications'] > 0:
            stats['command_detection_rate'] = stats['claude_commands_detected'] / stats['total_classifications']
            stats['failure_rate'] = stats['classification_failures'] / stats['total_classifications']
        else:
            stats['command_detection_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        stats['claude_available'] = self.claude_available
        return stats


# Example usage and testing
if __name__ == "__main__":
    # Test the LLM-based classifier
    classifier = IntentClassifier()
    
    # Test cases
    test_cases = [
        "Hey Claude, create a PRD for a mobile app",
        "Tell Claude to write a Python function",
        "Claude, please explain machine learning",
        "Ask Claude to review this code",
        "This is just normal speech",
        "Um, yeah, okay",
        "Claude is an AI assistant",  # Ambiguous case
        "Run Claude with the following prompt",
        "Hello there, how are you?",
        "Claude, help me debug this issue"
    ]
    
    print("Intent Classification Test Results:")
    print("=" * 50)
    
    for text in test_cases:
        result = classifier.detect_intent(text)
        
        print(f"\nInput: '{text}'")
        print(f"Is Claude Command: {result.is_claude_command}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Extracted Command: {result.command}")
        print(f"Keywords Found: {result.detected_keywords}")
        print("-" * 30)
    
    print(f"\nClassifier Stats: {classifier.get_stats()}")
