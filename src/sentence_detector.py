"""
Sentence Boundary Detection for Voice-driven Claude CLI automation system.

This module handles detecting complete sentences from partial transcription chunks
using Claude CLI to understand natural sentence boundaries in spoken language.
"""

import json
import logging
import subprocess
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
    Detects sentence boundaries in transcription text using Claude CLI.
    
    Uses Claude's natural language understanding to identify when transcribed
    speech represents complete thoughts/sentences vs partial fragments.
    """
    
    def __init__(self, claude_binary: str = "claude"):
        """Initialize the sentence boundary detector."""
        self.claude_binary = claude_binary
        self.stats = {
            'total_detections': 0,
            'sentences_completed': 0,
            'detection_failures': 0,
            'average_confidence': 0.0
        }
        
        # Test Claude availability
        self.claude_available = self._test_claude_availability()
        
        if not self.claude_available:
            logger.warning("Claude CLI not available - will use fallback sentence detection")
    
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

    def detect_sentence_boundary(self, text: str) -> SentenceBoundaryResult:
        """
        Detect sentence boundaries in the given text.
        
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
            # Use Claude CLI for intelligent sentence boundary detection
            if self.claude_available:
                result = self._detect_with_claude(cleaned_text)
            else:
                result = self._detect_with_fallback(cleaned_text)
            
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

    def _detect_with_claude(self, text: str) -> SentenceBoundaryResult:
        """Use Claude CLI for sentence boundary detection."""
        prompt = f"""You are analyzing transcribed speech to detect complete sentences.

Analyze this transcribed text: "{text}"

Your task is to:
1. Identify any complete sentences (complete thoughts that end naturally)
2. Identify any remaining fragment (incomplete thought at the end)
3. Consider natural speech patterns (people may pause mid-sentence, say "um", etc.)

Guidelines:
- A complete sentence expresses a complete thought
- Look for natural endings with punctuation or clear pauses
- Consider context clues like "and", "but", "so" that might continue thoughts
- Fragments are incomplete thoughts that sound like they're continuing

Respond with ONLY a JSON object in this exact format:
{{"completed_sentences": ["sentence 1", "sentence 2"], "remaining_fragment": "partial text", "confidence": 0.0-1.0, "is_complete": true/false}}

Where:
- completed_sentences: Array of complete sentences found
- remaining_fragment: Any incomplete text at the end (empty string if none)  
- confidence: How confident you are in the boundary detection (0.0-1.0)
- is_complete: Whether the entire text represents complete thought(s)
"""

        result = None
        try:
            result = subprocess.run(
                [self.claude_binary, "--print"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                logger.error(f"Claude CLI error: {result.stderr}")
                return self._detect_with_fallback(text)
                
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timeout during sentence detection")
            return self._detect_with_fallback(text)
        except Exception as e:
            logger.error(f"Claude CLI execution error: {e}")
            if result:
                logger.error(f"Raw response: {result.stdout}")
            return self._detect_with_fallback(text)
            
        # Parse JSON response (handle markdown code blocks)
        raw_output = result.stdout.strip()
            
        # Extract JSON from markdown code blocks - handle multiple code blocks
        json_content = raw_output
        if '```json' in raw_output:
            # Find the first JSON code block
            json_start = raw_output.find('```json') + 7
            json_end = raw_output.find('```', json_start)
            if json_end != -1:
                json_content = raw_output[json_start:json_end].strip()
            else:
                # No closing ``` found, take everything after ```json
                json_content = raw_output[json_start:].strip()
        elif raw_output.count('```') >= 2:
            # Find first complete code block (not necessarily JSON)
            json_start = raw_output.find('```') + 3
            json_end = raw_output.find('```', json_start)
            if json_end != -1:
                json_content = raw_output[json_start:json_end].strip()
        # If no code blocks or incomplete blocks, use raw output
            
        try:
            response = json.loads(json_content)
                
            return SentenceBoundaryResult(
                completed_sentences=response.get('completed_sentences', []),
                remaining_fragment=response.get('remaining_fragment', ''),
                confidence=float(response.get('confidence', 0.0)),
                is_complete=response.get('is_complete', False)
            )
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            if result:
                logger.error(f"Raw response: {result.stdout}")
            return self._detect_with_fallback(text)
        except Exception as e:
            logger.error(f"Claude sentence detection failed: {e}")
            return self._detect_with_fallback(text)
    
    def _detect_with_fallback(self, text: str) -> SentenceBoundaryResult:
        """Fallback sentence detection using simple heuristics."""
        import re
        
        # Simple sentence boundary detection using punctuation
        sentences = []
        remaining = text
        
        # Look for sentence endings
        sentence_pattern = r'([.!?]+)\s*'
        parts = re.split(sentence_pattern, text)
        
        current_sentence = ""
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and re.match(r'[.!?]+', parts[i + 1]):
                # Found sentence ending
                current_sentence += parts[i] + parts[i + 1]
                sentences.append(current_sentence.strip())
                current_sentence = ""
                i += 2
            else:
                current_sentence += parts[i]
                i += 1
        
        # What's left is the remaining fragment
        remaining_fragment = current_sentence.strip()
        
        # Confidence based on presence of clear sentence endings
        confidence = 0.8 if sentences else 0.3
        is_complete = bool(sentences) and not remaining_fragment
        
        return SentenceBoundaryResult(
            completed_sentences=sentences,
            remaining_fragment=remaining_fragment,
            confidence=confidence,
            is_complete=is_complete
        )

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
        
        stats['claude_available'] = self.claude_available
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