"""
Intent Classifier for Voice-driven Claude CLI automation system.

This module handles detecting Claude commands from voice transcriptions using
keyword matching and regex patterns. It provides confidence scoring and
command extraction without requiring external dependencies.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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
    Classifies voice transcriptions to detect Claude commands.
    
    Uses keyword matching and regex patterns to identify when the user
    wants to send a command to Claude CLI. Provides confidence scoring
    based on keyword presence and command structure.
    """
    
    def __init__(self):
        """Initialize the intent classifier with predefined patterns."""
        # Claude activation keywords (case-insensitive)
        self.claude_keywords = [
            'claude',
            'hey claude', 
            'tell claude',
            'ask claude',
            'claude please',
            'run claude',
            'execute claude'
        ]
        
        # Command extraction patterns
        self.command_patterns = [
            # "Tell Claude to [command]"
            r'tell\s+claude\s+to\s+(.+)',
            # "Ask Claude to [command]" 
            r'ask\s+claude\s+to\s+(.+)',
            # "Claude, [command]"
            r'claude,?\s+(.+)',
            # "Hey Claude, [command]"
            r'hey\s+claude,?\s+(.+)',
            # "Claude please [command]"
            r'claude\s+please\s+(.+)',
            # "Run Claude [command]"
            r'run\s+claude\s+(.+)',
            # "Execute Claude [command]"
            r'execute\s+claude\s+(.+)'
        ]
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.command_patterns
        ]
        
        # Common false positive filters
        self.false_positive_patterns = [
            r'^(um|uh|er|ah|hmm|like|you know)\s*$',
            r'^(yes|no|okay|ok)\s*$',
            r'^[^a-zA-Z]*$'  # Only punctuation/numbers
        ]
        
        self.false_positive_compiled = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.false_positive_patterns
        ]

    def detect_intent(self, text: str) -> IntentResult:
        """
        Detect if the given text contains a Claude command.
        
        Args:
            text: The transcribed voice text to analyze
            
        Returns:
            IntentResult with classification details and extracted command
        """
        if not text or not text.strip():
            return IntentResult(
                is_claude_command=False,
                command=None,
                confidence=0.0,
                original_text=text,
                detected_keywords=[]
            )
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Check for false positives
        if self._is_false_positive(cleaned_text):
            return IntentResult(
                is_claude_command=False,
                command=None,
                confidence=0.0,
                original_text=text,
                detected_keywords=[]
            )
        
        # Detect keywords
        detected_keywords = self._find_keywords(cleaned_text)
        
        # Extract command if keywords found
        command = None
        confidence = 0.0
        
        if detected_keywords:
            command = self._extract_command(cleaned_text)
            confidence = self._calculate_confidence(
                cleaned_text, detected_keywords, command
            )
        
        is_claude_command = confidence >= 0.6  # Threshold for classification
        
        return IntentResult(
            is_claude_command=is_claude_command,
            command=command,
            confidence=confidence,
            original_text=text,
            detected_keywords=detected_keywords
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text."""
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.strip().split())
        
        # Remove common speech artifacts
        artifacts = ['um', 'uh', 'er', 'ah', 'like', 'you know']
        for artifact in artifacts:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(artifact) + r'\b'
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned

    def _is_false_positive(self, text: str) -> bool:
        """Check if text matches false positive patterns."""
        for pattern in self.false_positive_compiled:
            if pattern.match(text.strip()):
                return True
        return False

    def _find_keywords(self, text: str) -> List[str]:
        """Find Claude keywords in the text."""
        detected = []
        text_lower = text.lower()
        
        for keyword in self.claude_keywords:
            if keyword in text_lower:
                detected.append(keyword)
        
        return detected

    def _extract_command(self, text: str) -> Optional[str]:
        """Extract the command portion from the text."""
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                command = match.group(1).strip()
                if command and len(command) > 0:
                    return command
        
        # Fallback: if "claude" is mentioned but no pattern matches,
        # try to extract everything after "claude" - but be more selective
        claude_match = re.search(r'claude\s+(.+)', text, re.IGNORECASE)
        if claude_match:
            command = claude_match.group(1).strip()
            
            # Remove common prefixes that might remain
            prefixes_to_remove = ['please', 'to', ',']
            for prefix in prefixes_to_remove:
                if command.lower().startswith(prefix):
                    command = command[len(prefix):].strip()
                    break
            
            # Only return command if it's not just a single common word
            common_non_commands = ['commands', 'is', 'are', 'was', 'were', 'the', 'a', 'an']
            if command and command.lower() not in common_non_commands and len(command) > 2:
                return command
        
        return None

    def _calculate_confidence(
        self, 
        text: str, 
        keywords: List[str], 
        command: Optional[str]
    ) -> float:
        """
        Calculate confidence score for Claude command detection.
        
        Confidence factors:
        - Keyword presence and specificity
        - Command extraction success
        - Text length and structure
        - Pattern matching quality
        """
        if not keywords:
            return 0.0
        
        confidence = 0.0
        
        # Base confidence from keywords
        if 'claude' in keywords:
            confidence += 0.4
        
        # Bonus for specific activation phrases
        specific_phrases = ['hey claude', 'tell claude', 'ask claude']
        for phrase in specific_phrases:
            if phrase in keywords:
                confidence += 0.3
                break
        
        # Bonus for successful command extraction
        if command and len(command.strip()) > 0:
            confidence += 0.3
            
            # Additional bonus for meaningful commands
            if len(command.strip()) > 5:  # Not just single words
                confidence += 0.1
        
        # Pattern matching bonus
        text_lower = text.lower()
        pattern_matched = False
        for pattern in self.compiled_patterns:
            if pattern.search(text_lower):
                pattern_matched = True
                confidence += 0.2
                break
        
        # Penalty for very short text
        if len(text.strip()) < 5:
            confidence *= 0.7
        
        # Ensure confidence is between 0 and 1
        return min(1.0, max(0.0, confidence))

    def get_stats(self) -> Dict:
        """Get statistics about the classifier configuration."""
        return {
            'keywords_count': len(self.claude_keywords),
            'patterns_count': len(self.command_patterns),
            'keywords': self.claude_keywords,
            'false_positive_filters': len(self.false_positive_patterns)
        }

    def add_keyword(self, keyword: str) -> None:
        """Add a new Claude activation keyword."""
        if keyword and keyword.lower() not in self.claude_keywords:
            self.claude_keywords.append(keyword.lower())
            logger.info(f"Added new keyword: {keyword}")

    def remove_keyword(self, keyword: str) -> bool:
        """Remove a Claude activation keyword."""
        keyword_lower = keyword.lower()
        if keyword_lower in self.claude_keywords:
            self.claude_keywords.remove(keyword_lower)
            logger.info(f"Removed keyword: {keyword}")
            return True
        return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize classifier
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
