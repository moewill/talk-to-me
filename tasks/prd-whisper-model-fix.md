# PRD: Fix Whisper Model Loading and Audio Processing System

## Introduction/Overview

The voice gateway system is experiencing continuous Whisper model loading failures, causing transcription errors and poor user experience during voice chat sessions. This feature will repair the existing Whisper model loading mechanism, implement proper error handling, and provide a robust audio processing foundation for the voice-driven Claude CLI system.

**Problem:** Whisper model fails to load with "don't know how to restore data location of torch.storage.UntypedStorage" error, causing all audio transcription attempts to fail.

**Goal:** Establish a reliable, locally-hosted transcription system that gracefully handles errors and provides consistent voice-to-text processing.

## Goals

1. **Fix Whisper Model Loading**: Resolve the torch/transformers compatibility issues preventing model initialization
2. **Robust Error Handling**: Eliminate error spam and provide meaningful feedback when transcription fails  
3. **Reliable Audio Processing**: Ensure consistent audio processing pipeline that doesn't crash the system
4. **Local Processing**: Maintain privacy and offline capability with local-only transcription
5. **Graceful Degradation**: Handle failures without breaking the entire voice chat system

## User Stories

- **As a developer testing the system**, I want the Whisper model to load successfully so that voice transcription works without errors
- **As a user of the voice chat**, I want clear feedback when audio processing fails instead of seeing continuous error messages
- **As a system operator**, I want the voice gateway to remain stable even when transcription components fail
- **As a privacy-conscious user**, I want all audio processing to happen locally without sending data to external services

## MVP Definition

**Minimum Viable Fix:**
1. Whisper model loads successfully on system startup
2. Audio transcription works for basic voice input
3. Error handling prevents continuous error spam
4. System remains stable when transcription fails
5. Clear status reporting for transcription capability

## Functional Requirements

### Must Have (P0)
1. **Model Loading Fix**: System must successfully load Whisper model without torch storage errors
2. **Error Suppression**: System must not spam console with repeated transcription failure messages
3. **Graceful Fallback**: When transcription fails, system must continue operating without crashing
4. **Status Reporting**: System must accurately report transcription capability status to clients
5. **Local Processing**: All transcription must happen on local machine without external API calls

### Should Have (P1) 
6. **Model Validation**: System should verify model integrity before attempting to use it
7. **Retry Logic**: System should attempt model reload after temporary failures
8. **Performance Monitoring**: System should track transcription success/failure rates
9. **Memory Management**: System should properly manage model memory usage

### Could Have (P2)
10. **Multiple Model Sizes**: Support for different Whisper model sizes (tiny, base, small, medium)
11. **Model Caching**: Efficient model loading and caching mechanisms
12. **Audio Format Validation**: Validate audio input format before processing

### Won't Have (P3)
- Cloud-based transcription APIs
- Real-time streaming transcription optimizations
- Multi-language model support
- Custom model fine-tuning

## Key Function Signatures

```python
async def load_model(model_name: str = "base") -> bool:
    """
    Load and initialize Whisper model
    Args:
        model_name: Whisper model size (tiny, base, small, medium, large)
    Returns:
        bool: True if model loaded successfully, False otherwise
    """

async def transcribe(audio_data: bytes) -> TranscriptionResult:
    """
    Transcribe audio data to text
    Args:
        audio_data: Raw audio bytes (16kHz, mono, PCM)
    Returns:
        TranscriptionResult: Contains success status, text, confidence, error details
    """

def get_model_status() -> dict:
    """
    Get current model loading status and capabilities
    Returns:
        dict: Model status, version, memory usage, error details
    """
```

## Interface Definitions

### AudioProcessor Interface
```python
class AudioProcessor:
    model_loaded: bool
    model_name: str
    error_count: int
    last_error: Optional[str]
    
    async def initialize() -> bool
    async def transcribe(audio_data: bytes) -> TranscriptionResult
    def get_stats() -> dict
    def reset_error_count() -> None
```

### TranscriptionResult Schema
```python
@dataclass
class TranscriptionResult:
    success: bool
    text: str = ""
    confidence: float = 0.0
    language: str = ""
    processing_time: float = 0.0
    error: str = ""
```

## API Contract Definitions

### WebSocket Error Messages
```json
{
  "type": "error",
  "message": "Transcription service unavailable",
  "error_code": "WHISPER_MODEL_FAILED",
  "timestamp": 1234567890.123,
  "retry_after": 30
}
```

### Processing Status Messages
```json
{
  "type": "processing", 
  "status": "model_loading|transcribing|failed|ready",
  "details": "Loading Whisper base model...",
  "audio_size": 8192
}
```

## Technical Standards

### Libraries & Dependencies
- **OpenAI Whisper**: Primary transcription engine (`pip install openai-whisper`)
- **PyTorch**: Use compatible version (check requirements.txt)
- **torchaudio**: For audio preprocessing
- **numpy**: Audio data manipulation

### Coding Standards
- Follow existing Python conventions in codebase
- Use async/await for I/O operations
- Implement proper logging with appropriate levels
- Handle exceptions gracefully without crashing main process
- Use type hints for all function signatures

### Error Handling Patterns
- Catch specific exceptions (torch errors, model loading failures)
- Implement exponential backoff for retry attempts
- Log errors at appropriate levels (ERROR for failures, WARNING for retries)
- Never let transcription failures crash the WebSocket server

## Non-Goals (Out of Scope)

- **Cloud Transcription**: No external API integrations (Google, OpenAI, etc.)
- **Real-time Optimizations**: Advanced streaming or chunk-based processing
- **Custom Models**: Training or fine-tuning custom Whisper models
- **Multi-language Support**: Focus on English transcription only
- **Audio Format Conversion**: Complex audio preprocessing (keep existing PCM format)
- **Performance Tuning**: GPU acceleration or model optimization

## Future Iterations

### Phase 2 - Enhanced Reliability
- Multiple model size options (tiny for speed, large for accuracy)
- Model health checks and automatic recovery
- Audio quality analysis and preprocessing

### Phase 3 - Advanced Features  
- Confidence-based filtering
- Noise reduction and audio enhancement
- Batch processing for efficiency

## Design Considerations

### Model Storage
- Store Whisper models in dedicated `models/` directory
- Check for existing model files before downloading
- Handle partial downloads and corrupted model files

### Memory Management
- Load model once at startup, keep in memory
- Monitor memory usage and implement cleanup if needed
- Consider model unloading/reloading for memory constraints

### Audio Processing Pipeline
```
Audio Input → Format Validation → Whisper Transcription → Result Processing → WebSocket Response
```

## Technical Considerations

### Dependencies
- **PyTorch Compatibility**: Ensure PyTorch version compatibility with Whisper
- **System Requirements**: Check available disk space for model files (~1GB for base model)
- **Memory Requirements**: Ensure sufficient RAM for model loading (~2GB recommended)

### Integration Points
- **VoiceGateway**: Update `_handle_audio_message()` to handle transcription failures gracefully
- **AudioProcessor**: Core component requiring the fixes
- **WebSocket Protocol**: Ensure error messages don't break client connections

### Known Issues to Address
1. **Torch Storage Error**: Specific error indicates version compatibility issues
2. **Model Download**: May need to re-download corrupted model files
3. **Memory Leaks**: Ensure proper cleanup of audio data and model resources

## Success Metrics

### Technical Metrics
- **Model Loading Success Rate**: 100% successful model loading on clean startup
- **Error Reduction**: Zero repeated error messages in logs
- **System Stability**: No WebSocket connection drops due to transcription failures
- **Memory Usage**: Stable memory consumption during audio processing

### User Experience Metrics
- **Error Feedback**: Clear, actionable error messages to users
- **Response Time**: Transcription attempts complete within 5 seconds or fail gracefully
- **Service Availability**: Voice chat remains available even when transcription is down

## Open Questions

1. **Model Storage Location**: Should models be stored in user directory or application directory?
2. **Model Size Selection**: Should we default to 'tiny' for faster loading or 'base' for better accuracy?
3. **Retry Strategy**: How many times should we retry model loading before giving up?
4. **Fallback Behavior**: Should we queue audio for later processing when model is unavailable?
5. **Version Pinning**: Should we pin specific versions of torch/whisper for stability?

---

**Priority**: High - Blocks core voice functionality
**Effort**: Medium - Primarily configuration and error handling fixes
**Risk**: Low - Well-defined problem with known solutions