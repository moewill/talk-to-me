"""
Sentence Boundary Detection for Voice-driven Claude CLI automation system.

This module handles detecting complete sentences from partial transcription chunks
using fast heuristic algorithms optimized for natural speech patterns.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class SentenceBoundaryResult:
    """Result of sentence boundary detection."""
    completed_sentences: List[str]
    remaining_fragment: str
    confidence: float
    is_complete: bool


class SentenceDetector:
    """
    Detects sentence boundaries in transcription text using fast heuristics.
    
    Uses pattern matching and speech recognition heuristics to identify when 
    transcribed speech represents complete thoughts/sentences vs partial fragments.
    Optimized for speed and reliability in voice-driven applications.
    """
    
    def __init__(self):
        """Initialize the sentence boundary detector."""
        self.stats = {
            'total_detections': 0,
            'sentences_completed': 0,
            'detection_failures': 0,
            'average_confidence': 0.0
        }
        
        logger.info("Initialized fast heuristic-based sentence detector")
    

    def detect_sentence_boundary(self, text: str) -> SentenceBoundaryResult:
        """
        Detect sentence boundaries in the given text using fast heuristics.
        
        Args:
            text: The transcribed text to analyze
            
        Returns:
            SentenceBoundaryResult with completed sentences and remaining fragment
        """
        if not text or not text.strip():
            return SentenceBoundaryResult(
                completed_sentences=[],
                remaining_fragment="",
                confidence=0.0,
                is_complete=False
            )
        
        cleaned_text = text.strip()
        
        # Handle very short inputs that are unlikely to be complete sentences
        if len(cleaned_text) < 3:
            return SentenceBoundaryResult(
                completed_sentences=[],
                remaining_fragment=cleaned_text,
                confidence=0.1,  # Very low confidence for short fragments
                is_complete=False
            )
        
        try:
            # Use fast heuristic-based sentence detection
            result = self._detect_with_heuristics(cleaned_text)
            
            # Update stats
            self.stats['total_detections'] += 1
            if result.completed_sentences:
                self.stats['sentences_completed'] += len(result.completed_sentences)
            
            self._update_avg_confidence(result.confidence)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in sentence boundary detection: {e}")
            self.stats['detection_failures'] += 1
            
            # Return safe fallback
            return SentenceBoundaryResult(
                completed_sentences=[],
                remaining_fragment=cleaned_text,
                confidence=0.0,
                is_complete=False
            )

    
    def _detect_with_heuristics(self, text: str) -> SentenceBoundaryResult:
        """Fast heuristic-based sentence detection optimized for voice input."""
        import re
        
        # Clean up common speech artifacts
        cleaned_text = self._clean_speech_text(text)
        
        # Split on strong sentence boundaries (period, exclamation, question mark)
        strong_endings = r'([.!?]+)\s*'
        parts = re.split(strong_endings, cleaned_text)
        
        sentences = []
        current_sentence = ""
        
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and re.match(r'[.!?]+', parts[i + 1]):
                # Found sentence ending punctuation
                current_sentence += parts[i] + parts[i + 1]
                sentence = current_sentence.strip()
                if sentence and len(sentence) > 2:  # Avoid very short fragments
                    sentences.append(sentence)
                current_sentence = ""
                i += 2
            else:
                current_sentence += parts[i]
                i += 1
        
        # What's left is the remaining fragment
        remaining_fragment = current_sentence.strip()
        
        # Check for implicit sentence completion patterns in speech
        if not sentences and remaining_fragment:
            if self._looks_like_complete_sentence(remaining_fragment):
                sentences.append(remaining_fragment)
                remaining_fragment = ""
        
        # Calculate confidence based on sentence endings and length
        confidence = self._calculate_confidence(sentences, remaining_fragment, text)
        is_complete = bool(sentences) and not remaining_fragment
        
        return SentenceBoundaryResult(
            completed_sentences=sentences,
            remaining_fragment=remaining_fragment,
            confidence=confidence,
            is_complete=is_complete
        )
    
    def _clean_speech_text(self, text: str) -> str:
        """Clean common speech artifacts from transcribed text."""
        import re
        
        # Remove common filler words at the start
        cleaned = re.sub(r'^(um|uh|er|ah|like|you know)\s+', '', text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _looks_like_complete_sentence(self, text: str) -> bool:
        """Check if text looks like a complete sentence based on speech patterns."""
        import re
        
        # Minimum length for a complete thought
        if len(text) < 5:
            return False
        
        # Common complete sentence patterns in speech
        complete_patterns = [
            r'^(please|could you|can you|would you|help me)',  # Requests
            r'^(what|how|when|where|why|who)',  # Questions
            r'^(I|you|we|they|it)\s+\w+',  # Subject-verb patterns
            r'^(let\'s|let me|show me)',  # Commands
            r'^(thank|thanks|okay|alright|yes|no)',  # Responses
        ]
        
        text_lower = text.lower()
        for pattern in complete_patterns:
            if re.match(pattern, text_lower):
                # Additional check: should have some substance (not just "I" or "you")
                word_count = len(text.split())
                if word_count >= 3:
                    return True
        
        # Check for natural conversation endings
        ending_patterns = [
            r'(right|okay|alright|done|finished|that\'s it)$',
            r'(please|thank you|thanks)$',
        ]
        
        for pattern in ending_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _calculate_confidence(self, sentences: list, remaining_fragment: str, original_text: str) -> float:
        """Calculate confidence score for sentence boundary detection."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if we found clear sentence endings
        if sentences:
            confidence += 0.3
        
        # Higher confidence if no remaining fragment
        if not remaining_fragment:
            confidence += 0.2
        
        # Adjust based on text length (longer text = more confident)
        text_length = len(original_text)
        if text_length > 50:
            confidence += 0.1
        elif text_length < 10:
            confidence -= 0.2
        
        # Adjust for punctuation presence
        import re
        if re.search(r'[.!?]', original_text):
            confidence += 0.1
        
        # Cap at 1.0
        return min(1.0, max(0.1, confidence))

    def _update_avg_confidence(self, confidence: float) -> None:
        """Update average confidence statistics."""
        if self.stats['total_detections'] == 1:
            self.stats['average_confidence'] = confidence
        else:
            total = self.stats['total_detections']
            current_avg = self.stats['average_confidence']
            self.stats['average_confidence'] = (current_avg * (total - 1) + confidence) / total
    
    def get_stats(self) -> dict:
        """Get sentence detection statistics."""
        stats = self.stats.copy()
        if stats['total_detections'] > 0:
            stats['completion_rate'] = stats['sentences_completed'] / stats['total_detections']
            stats['failure_rate'] = stats['detection_failures'] / stats['total_detections']
        else:
            stats['completion_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        stats['detection_method'] = 'heuristic'
        return stats


# Example usage and testing
if __name__ == "__main__":
    # Test the sentence detector
    detector = SentenceDetector()
    
    # Test cases
    test_cases = [
        "Hello, how are you today?",
        "I went to the store and bought some milk",
        "The weather is nice. I think I'll go for a walk.",
        "Um, I was wondering if you could help me with",
        "Thank you so much! Have a great day. See you later.",
        "I need to finish this project but I'm running out of",
    ]
    
    print("Sentence Boundary Detection Test Results:")
    print("=" * 60)
    
    for text in test_cases:
        result = detector.detect_sentence_boundary(text)
        
        print(f"\nInput: '{text}'")
        print(f"Completed Sentences: {result.completed_sentences}")
        print(f"Remaining Fragment: '{result.remaining_fragment}'")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Is Complete: {result.is_complete}")
        print("-" * 40)
    
    print(f"\nDetector Stats: {detector.get_stats()}")