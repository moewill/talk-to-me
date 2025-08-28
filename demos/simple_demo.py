#!/usr/bin/env python3
"""
Simple demo script for the Voice-driven Claude CLI automation system.

This script demonstrates basic functionality by testing individual components
without requiring a full WebSocket server setup.
"""

import asyncio
import logging
import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio_processor import AudioProcessor
from claude_interface import ClaudeInterface
from intent_classifier import IntentClassifier

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_audio_processor():
    """Demo the audio processor component."""
    print("\n" + "="*60)
    print("DEMO: Audio Processor")
    print("="*60)
    
    # Initialize audio processor with tiny model for speed
    processor = AudioProcessor(model_name="tiny")
    
    print("Loading Whisper model (this may take a moment)...")
    model_loaded = await processor.load_model()
    
    if model_loaded:
        print("✅ Whisper model loaded successfully")
        
        # Get stats
        stats = processor.get_stats()
        print(f"📊 Audio processor stats: {stats}")
        
        print("ℹ️  In a real scenario, you would send audio data to processor.transcribe(audio_bytes)")
        print("   For this demo, we'll skip actual audio processing due to complexity")
        
    else:
        print("❌ Failed to load Whisper model")
        print("   This is expected if OpenAI Whisper is not installed")


def demo_intent_classifier():
    """Demo the intent classifier component."""
    print("\n" + "="*60)
    print("DEMO: Intent Classifier")
    print("="*60)
    
    classifier = IntentClassifier()
    
    # Test various text inputs
    test_inputs = [
        "Hey Claude, write a Python function to calculate fibonacci numbers",
        "Tell Claude to create a new file with some content",
        "Claude please help me debug this code",
        "Just a regular conversation without any commands",
        "What's the weather like today?",
        "Ask Claude to explain how machine learning works",
        "claude write hello world",
        ""
    ]
    
    print("Testing intent classification on various inputs:")
    print("-" * 50)
    
    for text in test_inputs:
        result = classifier.detect_intent(text)
        
        status = "🟢 CLAUDE COMMAND" if result.is_claude_command else "🔴 NOT CLAUDE"
        confidence = f"{result.confidence:.2f}"
        
        print(f"{status} | Confidence: {confidence}")
        print(f"  Input: '{text}'")
        if result.is_claude_command:
            print(f"  Command: '{result.command}'")
            print(f"  Keywords: {result.detected_keywords}")
        print()
    
    # Get stats
    stats = classifier.get_stats()
    print(f"📊 Intent classifier stats: {stats}")


async def demo_claude_interface():
    """Demo the Claude interface component."""
    print("\n" + "="*60)
    print("DEMO: Claude Interface")
    print("="*60)
    
    interface = ClaudeInterface()
    
    # Test Claude CLI availability
    print("Testing Claude CLI availability...")
    test_result = await interface.test_connection()
    
    if test_result['available']:
        print("✅ Claude CLI is available")
        print(f"   Binary path: {test_result['binary_path']}")
        
        # Try executing a simple command
        print("\nExecuting a test command...")
        command = "write a simple hello world function in python"
        
        print(f"Command: '{command}'")
        result = await interface.execute_command(command)
        
        if result.success:
            print("✅ Command executed successfully")
            print(f"Execution time: {result.execution_time:.2f} seconds")
            print("Output preview:")
            print("-" * 30)
            # Show first 200 characters of output
            preview = result.output[:200] + "..." if len(result.output) > 200 else result.output
            print(preview)
            print("-" * 30)
        else:
            print("❌ Command execution failed")
            print(f"Error: {result.error}")
    else:
        print("❌ Claude CLI is not available")
        print(f"   Error: {test_result.get('error', 'Unknown error')}")
        print("   This is expected if Claude CLI is not installed or not in PATH")
    
    # Get stats
    stats = interface.get_stats()
    print(f"📊 Claude interface stats: {stats}")


async def demo_full_pipeline():
    """Demo the complete pipeline integration."""
    print("\n" + "="*60)
    print("DEMO: Full Pipeline Integration")
    print("="*60)
    
    # Initialize all components
    audio_processor = AudioProcessor(model_name="tiny")
    intent_classifier = IntentClassifier()
    claude_interface = ClaudeInterface()
    
    print("Simulating the complete voice-to-Claude pipeline...")
    
    # Simulate transcribed speech
    simulated_transcriptions = [
        "Claude write a function to reverse a string",
        "Hey Claude, can you create a simple calculator class?",
        "Tell Claude to explain what recursion is",
        "This is just normal conversation",
        "Claude help me understand async programming"
    ]
    
    for i, transcription in enumerate(simulated_transcriptions, 1):
        print(f"\n--- Pipeline Run {i} ---")
        print(f"🎤 Simulated transcription: '{transcription}'")
        
        # Step 1: Intent classification
        intent_result = intent_classifier.detect_intent(transcription)
        print(f"🧠 Intent classification: {'Claude command' if intent_result.is_claude_command else 'Regular text'}")
        print(f"   Confidence: {intent_result.confidence:.2f}")
        
        # Step 2: Execute Claude command if detected
        if intent_result.is_claude_command:
            print(f"⚡ Executing Claude command: '{intent_result.command}'")
            
            # Test Claude availability first
            test_result = await claude_interface.test_connection()
            if test_result['available']:
                result = await claude_interface.execute_command(intent_result.command)
                if result.success:
                    print(f"✅ Command completed in {result.execution_time:.2f}s")
                    # Show brief output preview
                    preview = result.output[:100] + "..." if len(result.output) > 100 else result.output
                    print(f"   Output preview: {preview}")
                else:
                    print(f"❌ Command failed: {result.error}")
            else:
                print("❌ Claude CLI not available - skipping execution")
        else:
            print("🔄 No Claude command detected - no action taken")
    
    print("\n📊 Final Statistics:")
    print(f"Intent Classifier: {intent_classifier.get_stats()}")
    print(f"Claude Interface: {claude_interface.get_stats()}")


def print_header():
    """Print demo header."""
    print("🎙️  Voice-driven Claude CLI Automation System")
    print("=" * 60)
    print("Simple Demo - Testing Individual Components")
    print("=" * 60)
    print()
    print("This demo tests each component individually to verify")
    print("that the voice-to-Claude pipeline is working correctly.")
    print()
    print("Note: Audio processing is simulated since it requires")
    print("actual audio input and OpenAI Whisper installation.")
    print()


async def main():
    """Run all demo components."""
    print_header()
    
    try:
        # Demo each component
        await demo_audio_processor()
        demo_intent_classifier()
        await demo_claude_interface()
        await demo_full_pipeline()
        
        print("\n" + "="*60)
        print("✅ Demo completed successfully!")
        print("="*60)
        print()
        print("Next steps:")
        print("1. Run the full demo with: python demos/full_demo.py")
        print("2. Start the voice gateway server with: python src/voice_gateway.py")
        print("3. Connect a WebSocket client to test real-time functionality")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo error details:")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
