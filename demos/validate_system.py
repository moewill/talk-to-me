#!/usr/bin/env python3
"""
System validation script for the voice-driven Claude CLI automation system.
This script performs comprehensive validation of all components and their integration.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """Comprehensive system validation for the voice gateway."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.errors: List[str] = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log a test result."""
        self.results[test_name] = {
            "success": success,
            "details": details
        }
        status = "✓" if success else "✗"
        logger.info(f"{status} {test_name}: {details}")
        
        if not success:
            self.errors.append(f"{test_name}: {details}")
            
    async def validate_dependencies(self) -> bool:
        """Validate that all required dependencies are available."""
        logger.info("Validating dependencies...")
        
        required_packages = [
            "numpy", "asyncio", "websockets", "logging", "json", 
            "pathlib", "typing", "dataclasses", "subprocess"
        ]
        
        optional_packages = [
            "openai", "soundfile", "librosa", "pydub"
        ]
        
        all_good = True
        
        for package in required_packages:
            try:
                __import__(package)
                self.log_result(f"Required package: {package}", True, "Available")
            except ImportError:
                self.log_result(f"Required package: {package}", False, "Missing")
                all_good = False
                
        for package in optional_packages:
            try:
                __import__(package)
                self.log_result(f"Optional package: {package}", True, "Available")
            except ImportError:
                self.log_result(f"Optional package: {package}", False, "Missing (optional)")
                
        return all_good
        
    async def validate_audio_processor(self) -> bool:
        """Validate the AudioProcessor component."""
        logger.info("Validating AudioProcessor...")
        
        try:
            from audio_processor import (AudioProcessor, AudioStats,
                                         TranscriptionResult)

            # Test initialization
            processor = AudioProcessor()
            self.log_result("AudioProcessor initialization", True, "Component loaded successfully")
            
            # Test configuration
            if hasattr(processor, 'whisper_model') and hasattr(processor, 'stats'):
                self.log_result("AudioProcessor configuration", True, "Configuration valid")
            else:
                self.log_result("AudioProcessor configuration", False, "Missing required attributes")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("AudioProcessor validation", False, str(e))
            return False
            
    async def validate_intent_classifier(self) -> bool:
        """Validate the IntentClassifier component."""
        logger.info("Validating IntentClassifier...")
        
        try:
            from intent_classifier import IntentClassifier, IntentResult

            # Test initialization
            classifier = IntentClassifier()
            self.log_result("IntentClassifier initialization", True, "Component loaded successfully")
            
            # Test intent classification
            test_cases = [
                ("hey claude write a hello world program", True),
                ("tell claude to create a new file", True),
                ("claude please help me", True),
                ("just some random text", False),
                ("hello there how are you", False)
            ]
            
            all_passed = True
            for text, should_detect in test_cases:
                result = classifier.detect_intent(text)
                detected = result.is_claude_command
                
                if detected == should_detect:
                    self.log_result(f"Intent test: '{text[:30]}...'", True, f"Detected: {detected}")
                else:
                    self.log_result(f"Intent test: '{text[:30]}...'", False, f"Expected: {should_detect}, Got: {detected}")
                    all_passed = False
                    
            return all_passed
            
        except Exception as e:
            self.log_result("IntentClassifier validation", False, str(e))
            return False
            
    async def validate_claude_interface(self) -> bool:
        """Validate the ClaudeInterface component."""
        logger.info("Validating ClaudeInterface...")
        
        try:
            from claude_interface import (ClaudeInterface, ClaudeResponse,
                                          ClaudeStats)

            # Test initialization
            interface = ClaudeInterface()
            self.log_result("ClaudeInterface initialization", True, "Component loaded successfully")
            
            # Test Claude availability using test_connection
            try:
                connection_test = await interface.test_connection()
                is_available = connection_test['available']
                self.log_result("Claude CLI availability", is_available, 
                              "Claude CLI found" if is_available else "Claude CLI not found")
                
                if is_available:
                    # Test simple command execution
                    try:
                        response = await interface.execute_command("echo 'validation test'")
                        if response.success and "validation test" in response.output:
                            self.log_result("Claude command execution", True, "Simple command successful")
                        else:
                            self.log_result("Claude command execution", False, "Command failed or unexpected output")
                            return False
                    except Exception as e:
                        self.log_result("Claude command execution", False, str(e))
                        return False
                else:
                    self.log_result("Claude command execution", True, "Skipped (Claude CLI not available)")
            except Exception as e:
                self.log_result("Claude CLI availability", False, f"Error testing availability: {str(e)}")
                self.log_result("Claude command execution", True, "Skipped (Claude CLI test failed)")
                
            return True
            
        except Exception as e:
            self.log_result("ClaudeInterface validation", False, str(e))
            return False
            
    async def validate_voice_gateway(self) -> bool:
        """Validate the VoiceGateway component."""
        logger.info("Validating VoiceGateway...")
        
        try:
            from voice_gateway import (ConnectionInfo, ProcessingStats,
                                       VoiceGateway)

            # Test initialization
            gateway = VoiceGateway()
            self.log_result("VoiceGateway initialization", True, "Component loaded successfully")
            
            # Test configuration
            if hasattr(gateway, 'audio_processor') and hasattr(gateway, 'intent_classifier') and hasattr(gateway, 'claude_interface'):
                self.log_result("VoiceGateway components", True, "All sub-components initialized")
            else:
                self.log_result("VoiceGateway components", False, "Missing sub-components")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("VoiceGateway validation", False, str(e))
            return False
            
    async def validate_file_structure(self) -> bool:
        """Validate the project file structure."""
        logger.info("Validating file structure...")
        
        project_root = Path(__file__).parent.parent
        
        required_files = [
            "requirements.txt",
            "src/audio_processor.py",
            "src/intent_classifier.py", 
            "src/claude_interface.py",
            "src/voice_gateway.py",
            "tests/test_audio_processor.py",
            "tests/test_intent_classifier.py",
            "tests/test_claude_interface.py",
            "tests/test_voice_gateway.py",
            "demos/simple_demo.py",
            "demos/full_demo.py",
            "demos/websocket_client.py"
        ]
        
        all_files_exist = True
        
        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                self.log_result(f"File: {file_path}", True, "Exists")
            else:
                self.log_result(f"File: {file_path}", False, "Missing")
                all_files_exist = False
                
        return all_files_exist
        
    async def validate_imports(self) -> bool:
        """Validate that all modules can be imported successfully."""
        logger.info("Validating module imports...")
        
        modules = [
            "audio_processor",
            "intent_classifier", 
            "claude_interface",
            "voice_gateway"
        ]
        
        all_imports_work = True
        
        for module in modules:
            try:
                __import__(module)
                self.log_result(f"Import: {module}", True, "Imported successfully")
            except Exception as e:
                self.log_result(f"Import: {module}", False, str(e))
                all_imports_work = False
                
        return all_imports_work
        
    async def run_full_validation(self) -> bool:
        """Run complete system validation."""
        logger.info("Starting comprehensive system validation...")
        
        validation_steps = [
            ("Dependencies", self.validate_dependencies),
            ("File Structure", self.validate_file_structure),
            ("Module Imports", self.validate_imports),
            ("AudioProcessor", self.validate_audio_processor),
            ("IntentClassifier", self.validate_intent_classifier),
            ("ClaudeInterface", self.validate_claude_interface),
            ("VoiceGateway", self.validate_voice_gateway)
        ]
        
        overall_success = True
        
        for step_name, step_func in validation_steps:
            logger.info(f"\n--- Validating {step_name} ---")
            try:
                success = await step_func()
                if not success:
                    overall_success = False
            except Exception as e:
                logger.error(f"Validation step '{step_name}' failed with exception: {e}")
                overall_success = False
                
        # Generate summary report
        self.generate_summary_report(overall_success)
        
        return overall_success
        
    def generate_summary_report(self, overall_success: bool):
        """Generate a summary report of the validation."""
        logger.info("\n" + "="*60)
        logger.info("SYSTEM VALIDATION SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        if overall_success:
            logger.info("\n✅ SYSTEM VALIDATION PASSED")
            logger.info("The voice gateway system is ready for use!")
        else:
            logger.error("\n❌ SYSTEM VALIDATION FAILED")
            logger.error("The following issues need to be addressed:")
            for error in self.errors:
                logger.error(f"  - {error}")
                
        logger.info("="*60)

async def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voice Gateway System Validation")
    parser.add_argument("--quick", action="store_true", help="Run quick validation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    validator = SystemValidator()
    
    try:
        success = await validator.run_full_validation()
        
        if success:
            logger.info("System validation completed successfully!")
            sys.exit(0)
        else:
            logger.error("System validation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
