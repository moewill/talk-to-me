# Task List: Voice-Driven Claude CLI - REALITY CHECK Implementation (v2)

**Based on:** `prd-voice-claude-cli-REALITY-CHECK.md`

**Current Status:** ~30% Complete with Critical Blockers

**Estimated Timeline:** 2-3 weeks (systematic fixes required)

## Relevant Files

- `requirements.txt` - Update dependency constraints to fix NumPy/PyTorch compatibility crisis
- `src/audio_processor.py` - Completely broken, needs dependency fixes and error handling  
- `src/voice_gateway.py` - Import failures prevent startup, needs relative import fixes
- `src/claude_interface.py` - Partially working but has critical timeout issues
- `src/intent_classifier.py` - Already working perfectly, production-ready
- `src/__init__.py` - Missing, needed for proper package structure
- `demos/simple_demo.py` - Broken demo with KeyError, needs fixing
- `demos/minimal_test.py` - New minimal working example needed
- `tests/test_dependencies.py` - Validate dependency compatibility
- `tests/test_audio_basic.py` - Basic audio processing validation
- `tests/test_claude_timeout.py` - Debug Claude CLI timeout issues
- `tests/test_integration.py` - End-to-end integration tests
- `setup.py` - Package installation configuration
- `.env.example` - Environment configuration template
- `docs/setup.md` - Environment setup documentation

### Notes

- **CRITICAL**: NumPy version 2.x breaks Whisper/PyTorch - must downgrade to numpy<2
- System dependency required: FFmpeg (`brew install ffmpeg` on macOS)
- Virtual environment strongly recommended due to dependency conflicts
- Whisper models are 1-5GB and should not be committed to git
- Tests must validate each component independently before attempting integration
- Use `python -m pytest tests/ -v` to run test suite with verbose output

## Tasks

- [ ] 1.0 Emergency Dependency Crisis Resolution
  - [ ] 1.1 Create fresh virtual environment to isolate dependency conflicts
  - [ ] 1.2 Document current broken state with `pip freeze > broken_requirements.txt`
  - [ ] 1.3 Pin NumPy to `numpy<2.0` in requirements.txt to fix Whisper compatibility
  - [ ] 1.4 Install FFmpeg system dependency (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Ubuntu)
  - [ ] 1.5 Reinstall PyTorch with NumPy 1.x compatibility
  - [ ] 1.6 Test Whisper model download and loading in isolation
  - [ ] 1.7 Create dependency validation script that tests all critical imports
  - [ ] 1.8 Update requirements.txt with working version constraints
  - [ ] 1.9 Document exact working environment setup in setup.md

- [ ] 2.0 Rebuild Audio Processing Foundation
  - [ ] 2.1 Create minimal Whisper test script to verify model loading works
  - [ ] 2.2 Debug "Weights only load failed" error with different model sizes
  - [ ] 2.3 Implement graceful fallback when Whisper dependencies unavailable
  - [ ] 2.4 Add comprehensive error handling in AudioProcessor.__init__()
  - [ ] 2.5 Test audio file format conversion with working FFmpeg
  - [ ] 2.6 Create simple audio transcription test with known audio file
  - [ ] 2.7 Research and implement alternative STT libraries as backup (speech_recognition, vosk)
  - [ ] 2.8 Add proper audio validation and preprocessing
  - [ ] 2.9 Create unit tests for audio processing components
  - [ ] 2.10 Optimize Whisper model selection for speed vs accuracy tradeoffs

- [ ] 3.0 Fix Critical Import and Module Structure Issues
  - [ ] 3.1 Create proper `src/__init__.py` file to establish package structure
  - [ ] 3.2 Convert all relative imports to absolute imports in voice_gateway.py
  - [ ] 3.3 Fix module path resolution across all components
  - [ ] 3.4 Test each component can be imported independently without crashes
  - [ ] 3.5 Create setup.py for proper package installation and path handling
  - [ ] 3.6 Fix demo script import errors and path issues
  - [ ] 3.7 Validate VoiceGateway can be imported and instantiated
  - [ ] 3.8 Add proper error handling for missing component dependencies
  - [ ] 3.9 Create import validation test suite

- [ ] 4.0 Debug and Resolve Claude Interface Timeout Problems
  - [ ] 4.1 Investigate why Claude CLI commands hang in Python subprocess (30+ seconds)
  - [ ] 4.2 Test Claude CLI execution with different subprocess configurations
  - [ ] 4.3 Compare direct command line execution vs Python subprocess behavior
  - [ ] 4.4 Implement proper timeout handling with process termination
  - [ ] 4.5 Add comprehensive subprocess logging and debugging
  - [ ] 4.6 Test different Claude CLI command formats and arguments
  - [ ] 4.7 Implement retry logic for failed Claude executions
  - [ ] 4.8 Create Claude CLI health check and validation tests
  - [ ] 4.9 Fix async subprocess handling to prevent hanging
  - [ ] 4.10 Add process monitoring and cleanup for zombie processes

- [ ] 5.0 Systematic Integration and Validation
  - [ ] 5.1 Create minimal working demo testing each component independently
  - [ ] 5.2 Fix VoiceGateway WebSocket server startup with working dependencies
  - [ ] 5.3 Test basic WebSocket connection handling without audio processing
  - [ ] 5.4 Integrate working IntentClassifier with fixed ClaudeInterface
  - [ ] 5.5 Add working AudioProcessor to complete the voice processing pipeline
  - [ ] 5.6 Create end-to-end integration test with real audio input
  - [ ] 5.7 Implement comprehensive error recovery and graceful degradation
  - [ ] 5.8 Add system health monitoring and component status reporting
  - [ ] 5.9 Performance testing to achieve <10 second end-to-end latency
  - [ ] 5.10 Create comprehensive logging and debugging infrastructure
  - [ ] 5.11 Document final system architecture and known limitations
  - [ ] 5.12 Create production deployment guide with dependency requirements