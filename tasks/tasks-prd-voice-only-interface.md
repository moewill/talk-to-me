# Tasks: Voice-Only Chat Interface with Real-time Transcription

## Relevant Files

- `test.html` - Main frontend interface with voice-only UI, auto-connection, debug toggle, and real-time transcription display
- `src/voice_gateway.py` - Backend WebSocket server with sentence boundary detection and streaming transcription support
- `src/sentence_detector.py` - New module for Claude CLI-based sentence boundary detection
- `src/audio_processor.py` - Audio processing with streaming transcription integration
- `src/intent_classifier.py` - LLM-powered intent classification for natural language commands
- `src/claude_interface.py` - Claude CLI interface for command execution

### Notes

- The existing codebase uses pure JavaScript in `test.html` with WebSocket communication to Python backend
- Backend uses asyncio WebSocket server with existing audio processing and Claude CLI integration
- Focus on maintaining existing architecture while adding new features

## Tasks

- [x] 1.0 Frontend UI Cleanup and Auto-Connection
  - [x] 1.1 Remove text input field and send button from HTML
  - [x] 1.2 Remove start/stop voice chat buttons from HTML
  - [x] 1.3 Update CSS to hide/remove manual control elements
  - [x] 1.4 Implement automatic WebSocket connection on page load
  - [x] 1.5 Add automatic microphone permission request with user explanation
  - [x] 1.6 Implement automatic voice chat activation after connection success
  - [x] 1.7 Remove manual connection logic and event handlers for removed buttons

- [x] 2.0 Connection Status and Error Management
  - [x] 2.1 Create connection status display element at top of chat window
  - [x] 2.2 Implement connection state tracking (connecting/connected/error/disconnected)
  - [x] 2.3 Add status message updates for different connection states
  - [x] 2.4 Implement error message display that replaces status temporarily
  - [x] 2.5 Add visual styling for different status states (colors, icons)
  - [x] 2.6 Implement connection retry logic with exponential backoff
  - [x] 2.7 Add microphone-specific error handling and messaging

- [x] 3.0 Debug Toggle System Implementation
  - [x] 3.1 Create floating debug toggle button (visible, bottom-right corner)
  - [x] 3.2 Implement debug state management (off by default)
  - [x] 3.3 Add debug message filtering logic for different message types
  - [x] 3.4 Update message display to respect debug toggle state
  - [x] 3.5 Add visual styling for debug button (on/off states)
  - [x] 3.6 Implement debug toggle persistence within session (not across reloads)
  - [x] 3.7 Add keyboard shortcut support (Ctrl+D) for debug toggle

- [x] 4.0 Backend Sentence Boundary Detection
  - [x] 4.1 Add sentence boundary detection function using Claude CLI integration
  - [x] 4.2 Implement transcription chunk processing for partial vs complete sentences
  - [x] 4.3 Add new WebSocket message types for streaming transcription
  - [x] 4.4 Update voice gateway to use sentence boundary detection during transcription
  - [x] 4.5 Add sentence completion timeout handling for unclear boundaries
  - [x] 4.6 Implement confidence scoring for sentence boundary decisions
  - [x] 4.7 Add logging and debugging support for sentence boundary detection

- [x] 5.0 Real-time Transcription with In-Place Updates
  - [x] 5.1 Implement partial transcription display with in-place updates
  - [x] 5.2 Add visual typing indicators during active transcription
  - [x] 5.3 Create sentence completion logic for finalizing transcriptions
  - [x] 5.4 Update message formatting with colors and timestamps
  - [x] 5.5 Add smooth DOM updates to prevent flickering during transcription
  - [x] 5.6 Implement message history limits (100 messages) for performance
  - [x] 5.7 Add transcription confidence indicators and error states
  - [x] 5.8 Implement automatic scrolling behavior for new messages