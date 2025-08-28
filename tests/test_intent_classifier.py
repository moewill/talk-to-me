"""
Comprehensive tests for the IntentClassifier module.
"""

from unittest.mock import Mock, patch

import pytest
from src.intent_classifier import IntentClassifier, IntentResult


@pytest.fixture
def intent_classifier():
    """Create an IntentClassifier instance for testing."""
    return IntentClassifier()


class TestIntentClassifier:
    """Test cases for IntentClassifier functionality."""
    
    def test_initialization(self, intent_classifier):
        """Test IntentClassifier initialization."""
        assert len(intent_classifier.claude_keywords) > 0
        assert "claude" in intent_classifier.claude_keywords
        assert intent_classifier.stats.total_processed == 0
        assert intent_classifier.stats.claude_commands_detected == 0
    
    def test_detect_intent_claude_command(self, intent_classifier):
        """Test detection of Claude commands."""
        test_cases = [
            "Hey Claude, write a function to calculate fibonacci",
            "Tell Claude to create a Python script",
            "Claude please help me with this code",
            "Ask Claude to explain this algorithm",
            "Claude, run this command for me"
        ]
        
        for text in test_cases:
            result = intent_classifier.detect_intent(text)
            
            assert isinstance(result, IntentResult)
            assert result.is_claude_command is True
            assert result.command is not None
            assert len(result.command) > 0
            assert result.confidence > 0.0
            assert result.original_text == text
            assert len(result.detected_keywords) > 0
    
    def test_detect_intent_non_claude_command(self, intent_classifier):
        """Test detection of non-Claude commands."""
        test_cases = [
            "Hello, how are you today?",
            "What's the weather like?",
            "Can you help me with something?",
            "I need assistance with my project",
            "This is just a regular conversation"
        ]
        
        for text in test_cases:
            result = intent_classifier.detect_intent(text)
            
            assert isinstance(result, IntentResult)
            assert result.is_claude_command is False
            assert result.command == ""
            assert result.confidence >= 0.0
            assert result.original_text == text
            assert len(result.detected_keywords) == 0
    
    def test_detect_intent_empty_text(self, intent_classifier):
        """Test detection with empty text."""
        result = intent_classifier.detect_intent("")
        
        assert isinstance(result, IntentResult)
        assert result.is_claude_command is False
        assert result.command == ""
        assert result.confidence == 0.0
        assert result.original_text == ""
        assert len(result.detected_keywords) == 0
    
    def test_detect_intent_whitespace_only(self, intent_classifier):
        """Test detection with whitespace-only text."""
        result = intent_classifier.detect_intent("   \t\n  ")
        
        assert isinstance(result, IntentResult)
        assert result.is_claude_command is False
        assert result.command == ""
        assert result.confidence == 0.0
    
    def test_extract_command_simple(self, intent_classifier):
        """Test command extraction for simple cases."""
        test_cases = [
            ("Claude write a function", "write a function"),
            ("Hey Claude, create a script", "create a script"),
            ("Tell Claude to help me", "help me"),
            ("Ask Claude please explain this", "explain this")
        ]
        
        for input_text, expected_command in test_cases:
            result = intent_classifier._extract_command(input_text)
            assert expected_command in result.lower()
    
    def test_extract_command_complex(self, intent_classifier):
        """Test command extraction for complex cases."""
        text = "Hey Claude, can you please write a Python function that calculates the factorial of a number?"
        result = intent_classifier._extract_command(text)
        
        assert "write a python function" in result.lower()
        assert "factorial" in result.lower()
        assert len(result) > 10  # Should be substantial command
    
    def test_extract_command_no_keyword(self, intent_classifier):
        """Test command extraction when no keywords are present."""
        text = "Just some regular text without any triggers"
        result = intent_classifier._extract_command(text)
        
        assert result == text  # Should return original text
    
    def test_calculate_confidence_high(self, intent_classifier):
        """Test confidence calculation for high-confidence detection."""
        detected_keywords = ["claude", "tell claude"]
        command_length = 50
        
        confidence = intent_classifier._calculate_confidence(detected_keywords, command_length)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high confidence
    
    def test_calculate_confidence_medium(self, intent_classifier):
        """Test confidence calculation for medium-confidence detection."""
        detected_keywords = ["claude"]
        command_length = 20
        
        confidence = intent_classifier._calculate_confidence(detected_keywords, command_length)
        
        assert 0.0 <= confidence <= 1.0
        assert 0.3 <= confidence <= 0.8  # Should be medium confidence
    
    def test_calculate_confidence_low(self, intent_classifier):
        """Test confidence calculation for low-confidence detection."""
        detected_keywords = []
        command_length = 5
        
        confidence = intent_classifier._calculate_confidence(detected_keywords, command_length)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.3  # Should be low confidence
    
    def test_filter_false_positives_speech_artifacts(self, intent_classifier):
        """Test filtering of speech artifacts and false positives."""
        test_cases = [
            "um claude uh",  # Should be filtered due to speech artifacts
            "claude uh um er",  # Should be filtered
            "claude",  # Should be filtered due to being too short
            "cl claude clau"  # Should be filtered due to repetition
        ]
        
        for text in test_cases:
            result = intent_classifier._filter_false_positives(text)
            assert result is False
    
    def test_filter_false_positives_valid_commands(self, intent_classifier):
        """Test that valid commands pass the false positive filter."""
        test_cases = [
            "claude write a function",
            "hey claude please help me with this code",
            "tell claude to create a new file",
            "claude can you explain this algorithm"
        ]
        
        for text in test_cases:
            result = intent_classifier._filter_false_positives(text)
            assert result is True
    
    def test_detect_keywords_case_insensitive(self, intent_classifier):
        """Test that keyword detection is case insensitive."""
        test_cases = [
            "CLAUDE write something",
            "Hey CLAUDE please help",
            "tell CLAUDE to do this",
            "Claude PLEASE explain"
        ]
        
        for text in test_cases:
            keywords = intent_classifier._detect_keywords(text)
            assert len(keywords) > 0
            assert any("claude" in kw.lower() for kw in keywords)
    
    def test_detect_keywords_multiple(self, intent_classifier):
        """Test detection of multiple keywords in a single text."""
        text = "Hey Claude, tell Claude to run Claude commands"
        keywords = intent_classifier._detect_keywords(text)
        
        # Should detect multiple instances of claude-related keywords
        assert len(keywords) >= 2
        assert "claude" in [kw.lower() for kw in keywords]
    
    def test_detect_keywords_none_found(self, intent_classifier):
        """Test keyword detection when no keywords are present."""
        text = "This is just regular text without any triggers"
        keywords = intent_classifier._detect_keywords(text)
        
        assert len(keywords) == 0
    
    def test_get_stats(self, intent_classifier):
        """Test statistics retrieval."""
        # Manually update some stats
        intent_classifier.stats.total_processed = 10
        intent_classifier.stats.claude_commands_detected = 7
        intent_classifier.stats.false_positives_filtered = 2
        
        stats = intent_classifier.get_stats()
        
        assert stats["total_processed"] == 10
        assert stats["claude_commands_detected"] == 7
        assert stats["false_positives_filtered"] == 2
        assert "detection_rate" in stats
        assert "average_confidence" in stats
    
    def test_detect_intent_updates_stats(self, intent_classifier):
        """Test that intent detection updates statistics."""
        initial_count = intent_classifier.stats.total_processed
        
        # Process a Claude command
        intent_classifier.detect_intent("Claude write a function")
        
        assert intent_classifier.stats.total_processed == initial_count + 1
        assert intent_classifier.stats.claude_commands_detected >= 1
    
    def test_confidence_bounds(self, intent_classifier):
        """Test that confidence values are always within valid bounds."""
        test_cases = [
            "Claude write a very long command with lots of details and explanations",
            "claude",
            "hey claude",
            "tell claude to do something simple",
            "",
            "no keywords here at all"
        ]
        
        for text in test_cases:
            result = intent_classifier.detect_intent(text)
            assert 0.0 <= result.confidence <= 1.0
    
    def test_command_extraction_preserves_important_words(self, intent_classifier):
        """Test that command extraction preserves important words."""
        text = "Hey Claude, please write a Python function to parse JSON data"
        result = intent_classifier._extract_command(text)
        
        important_words = ["write", "python", "function", "parse", "json", "data"]
        for word in important_words:
            assert word.lower() in result.lower()
    
    def test_keyword_variations(self, intent_classifier):
        """Test detection of various keyword combinations."""
        test_cases = [
            ("hey claude", True),
            ("tell claude", True),
            ("ask claude", True),
            ("claude please", True),
            ("run claude", True),
            ("execute claude", True),
            ("just some text", False),
            ("claude-like but not claude", False)
        ]
        
        for text, should_detect in test_cases:
            result = intent_classifier.detect_intent(text)
            assert result.is_claude_command == should_detect
    
    def test_edge_cases(self, intent_classifier):
        """Test various edge cases."""
        edge_cases = [
            None,  # None input
            123,   # Non-string input
            [],    # List input
            {}     # Dict input
        ]
        
        for case in edge_cases:
            try:
                result = intent_classifier.detect_intent(case)
                # If it doesn't raise an exception, it should return a valid result
                assert isinstance(result, IntentResult)
                assert result.is_claude_command is False
            except (TypeError, AttributeError):
                # It's acceptable to raise an exception for invalid input types
                pass
