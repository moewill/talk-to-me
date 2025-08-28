# Task List: Voice-Driven Claude CLI - REALITY CHECK Implementation

**Based on:** `prd-voice-claude-cli-REALITY-CHECK.md`

**Current Status:** ~30% Complete with Critical Blockers

**Estimated Timeline:** 2-3 weeks (systematic fixes required)

## Relevant Files

- `requirements.txt` - Update dependency constraints to fix NumPy/PyTorch compatibility issues
- `src/audio_processor.py` - Fix Whisper model loading and audio processing functionality  
- `src/voice_gateway.py` - Fix relative import errors and enable WebSocket server startup
- `src/claude_interface.py` - Fix timeout issues and improve subprocess handling
- `src/intent_classifier.py` - Already working, may need minor integration updates
- `src/__init__.py` - Create proper package structure for absolute imports
- `demos/simple_demo.py` - Fix demo script to validate component functionality
- `demos/minimal_test.py` - Create new minimal working example
- `tests/test_dependencies.py` - Create dependency validation test
- `tests/test_audio_basic.py` - Basic audio processing tests
- `tests/test_integration.py` - End-to-end integration tests
- `setup.py` - Create proper package installation configuration
- `.gitignore` - Update to exclude model files and cache

### Notes

- System dependencies required: FFmpeg must be installed (`brew install ffmpeg` on macOS)
- Virtual environment strongly recommended due to NumPy compatibility issues
- Tests should validate each component independently before integration
- Use `python -m pytest tests/` to run test suite
- Model files are large (1-5GB) and should not be committed to git

## Tasks

- [ ] 1.0 Fix Foundation Dependencies and Environment
  - [ ] 1.1 Create new virtual environment to isolate dependency issues
  - [ ] 1.2 Pin NumPy to version <2.0 in requirements.txt to fix Whisper compatibility
  - [ ] 1.3 Install FFmpeg system dependency (`brew install ffmpeg` on macOS)
  - [ ] 1.4 Test Whisper model loading in isolation with fixed dependencies
  - [ ] 1.5 Update requirements.txt with proper version constraints for all packages
  - [ ] 1.6 Create dependency validation test script
  - [ ] 1.7 Document environment setup process in README

- [ ] 2.0 Repair Audio Processing Component
  - [ ] 2.1 Create minimal Whisper test script to verify model loading works
  - [ ] 2.2 Fix AudioProcessor initialization to handle dependency failures gracefully
  - [ ] 2.3 Implement fallback audio processing using alternative STT libraries
  - [ ] 2.4 Test audio format conversion (WAV, MP3) with fixed FFmpeg
  - [ ] 2.5 Add comprehensive error handling for missing dependencies
  - [ ] 2.6 Create unit tests for audio transcription functionality
  - [ ] 2.7 Optimize Whisper model size selection for performance vs accuracy

- [ ] 3.0 Fix Module Structure and Imports
  - [ ] 3.1 Create proper `src/__init__.py` file for package structure
  - [ ] 3.2 Convert relative imports to absolute imports in voice_gateway.py
  - [ ] 3.3 Fix module path issues across all components
  - [ ] 3.4 Create setup.py for proper package installation
  - [ ] 3.5 Test all module imports work independently
  - [ ] 3.6 Fix demo script import paths and execution
  - [ ] 3.7 Validate VoiceGateway can be imported without errors

- [ ] 4.0 Resolve Claude Interface Issues
  - [ ] 4.1 Investigate why Claude CLI commands timeout in Python subprocess
  - [ ] 4.2 Test different subprocess execution approaches (shell=True, direct execution)
  - [ ] 4.3 Implement proper timeout handling with process termination
  - [ ] 4.4 Add retry logic for failed Claude CLI executions
  - [ ] 4.5 Create Claude CLI validation test with known working commands
  - [ ] 4.6 Fix async subprocess handling to prevent hanging
  - [ ] 4.7 Add comprehensive logging for subprocess debugging

- [ ] 5.0 Integrate Components and Create Working System
  - [ ] 5.1 Create minimal working demo that tests each component independently
  - [ ] 5.2 Fix VoiceGateway WebSocket server startup with working components
  - [ ] 5.3 Test basic WebSocket message handling without audio
  - [ ] 5.4 Integrate working IntentClassifier with fixed ClaudeInterface
  - [ ] 5.5 Add working AudioProcessor to complete voice pipeline
  - [ ] 5.6 Create end-to-end integration test with real audio input
  - [ ] 5.7 Add error recovery and graceful degradation for component failures
  - [ ] 5.8 Performance testing and optimization for <10 second latency target
  - [ ] 5.9 Create comprehensive system health monitoring and logging
  - [ ] 5.10 Document final system architecture and deployment instructions