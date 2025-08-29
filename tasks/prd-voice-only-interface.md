# PRD: Voice-Only Chat Interface with Real-time Transcription

## Introduction/Overview
Transform the current voice chat application into a streamlined, voice-only interface that provides natural real-time transcription and automatic connection management. This feature eliminates manual controls and text input to create a seamless voice conversation experience with Claude AI, similar to modern voice assistants.

## Goals
1. **Simplify User Experience**: Remove manual controls (text input, voice buttons) for automatic voice-only operation
2. **Natural Conversation Flow**: Display transcriptions as complete, natural sentences rather than fragmented buffer outputs  
3. **Intelligent Debug Control**: Provide optional debug visibility without cluttering the main conversation
4. **Seamless Connection**: Automatically establish voice connection with clear status feedback
5. **Real-time Feedback**: Show live transcription progress with visual indicators

## User Stories
- **As a user**, I want the app to automatically connect when I load the page so I can start speaking immediately
- **As a user**, I want my speech to appear as natural sentences in the chat so it feels like a normal conversation
- **As a developer/power user**, I want to toggle debug information when troubleshooting without affecting normal users
- **As a user**, I want clear status indication when something goes wrong so I know if the system is working
- **As a user**, I want to see my speech being transcribed in real-time so I get immediate feedback

## MVP Definition
A voice-only interface that:
- Auto-connects to voice chat on page load
- Shows real-time transcription as natural sentences with in-place updates
- Displays connection status clearly
- Provides hidden debug toggle for developers
- Removes all text input and manual voice controls

## Functional Requirements

### Must Have (MVP)
1. **Auto-Connection**: System must automatically attempt voice connection when page loads
2. **Microphone Permission**: System must request microphone access with clear explanation before requesting permission  
3. **Voice-Only Interface**: Remove text input field and send button completely
4. **Auto Voice Activation**: Remove start/stop voice chat buttons - voice should be always active when connected
5. **Real-time Sentence Display**: Transcribed speech must appear as complete sentences using LLM/Claude sentence boundary detection
6. **In-Place Transcription Updates**: Partial transcription must update in place with visual typing indicator until sentence completion
7. **Connection Status Display**: Status must appear at top of chat window showing connection state
8. **Error Status Integration**: Errors must replace status message temporarily with clear error indication
9. **Debug Toggle**: Visible floating button to toggle debug message visibility (debug messages off by default)
10. **Debug Message Types**: All JSON/technical messages, system/processing messages, and connection/performance metrics when debug enabled
11. **Message Formatting**: Different colors for user speech vs Claude responses with timestamps

### Should Have
12. **Connection Retry Logic**: Automatic reconnection attempts with exponential backoff
13. **Microphone Error Handling**: Clear messaging when microphone access fails or disconnects
14. **Performance Optimization**: Limit message history to last 100 messages for memory management

### Could Have  
15. **Visual Transcription Indicators**: Animated typing dots or cursor during active transcription
16. **Connection Quality Indicator**: Visual indicator of connection strength/latency
17. **Keyboard Shortcuts**: Debug toggle via keyboard shortcut (e.g., Ctrl+D)

### Won't Have (This Release)
18. **Text Input Fallback**: No text-based interaction options
19. **Voice Recording/Playback**: No ability to save or replay conversations
20. **Multi-user Support**: Single user conversation only

## Key Function Signatures

```javascript
// Auto-connection management
async function initializeVoiceConnection(): Promise<ConnectionResult>
function handleConnectionStatus(status: ConnectionStatus): void

// Real-time transcription processing  
function processTranscriptionStream(chunk: TranscriptionChunk): void
function completeSentence(sentence: string): void
function updatePartialTranscription(partial: string): void

// Debug toggle functionality
function toggleDebugMode(): void
function shouldDisplayDebugMessage(messageType: string): boolean

// Sentence boundary detection (server-side)
function detectSentenceBoundary(transcription: string): SentenceBoundaryResult
```

## Interface Definitions

```typescript
interface ConnectionStatus {
  state: 'connecting' | 'connected' | 'error' | 'disconnected';
  message: string;
  errorCode?: string;
}

interface TranscriptionChunk {
  partial: string;
  isComplete: boolean;
  confidence: number;
  sentenceBoundary?: boolean;
}

interface SentenceBoundaryResult {
  completedSentences: string[];
  remainingFragment: string;
  confidence: number;
}
```

## API Contract Definitions

### WebSocket Message Extensions
```json
{
  "type": "transcription_stream",
  "partial_text": "Hello, how are you",
  "is_sentence_complete": false,
  "sentence_boundary_confidence": 0.8
}

{
  "type": "sentence_complete", 
  "complete_sentence": "Hello, how are you today?",
  "confidence": 0.95
}
```

## Technical Standards
- **Frontend**: Pure JavaScript (no framework changes) following existing patterns
- **WebSocket Library**: Continue using existing websockets implementation with asyncio.server
- **State Management**: Use existing connection management patterns
- **Error Handling**: Follow current error propagation patterns
- **Logging**: Maintain existing debug logging levels
- **Code Style**: Follow existing JavaScript formatting and naming conventions

## Non-Goals (Out of Scope)
- Text-based input methods or fallbacks
- Voice recording/playback capabilities  
- Multi-user or group conversation support
- Voice settings/configuration UI
- Conversation history persistence
- Mobile-specific optimizations
- Accessibility features beyond basic screen reader support

## Future Iterations
- **Voice Activity Detection**: Smarter microphone activation based on voice activity
- **Speaker Identification**: Distinguish between multiple speakers
- **Conversation Templates**: Pre-defined conversation flows or prompts
- **Voice Synthesis**: Text-to-speech for Claude responses
- **Advanced Debug Panel**: Detailed performance metrics and connection diagnostics
- **Conversation Export**: Save/export conversation transcripts

## Design Considerations
- **Status Bar**: Clean, minimal status indicator at top of chat window
- **Debug Toggle**: Visible floating button (bottom right corner) with debug messages off by default  
- **Message Styling**: Clear visual distinction between user speech (blue background) and Claude responses (gray background)
- **Typing Indicators**: Subtle animation during partial transcription updates
- **Error States**: Red status bar with clear error messaging
- **Loading States**: Connection progress indication during initial setup

## Technical Considerations
- **Sentence Boundary Detection**: Implement server-side using Claude CLI to analyze transcription chunks and determine natural sentence breaks
- **Buffer Management**: Maintain partial transcription state on client-side for smooth in-place updates
- **WebSocket Protocol**: Extend existing message types to support streaming transcription updates
- **Performance**: Implement message history limits and efficient DOM updates for long conversations
- **Error Recovery**: Robust reconnection logic with user-friendly status messages

## Success Metrics
- **User Engagement**: 90% of users successfully establish voice connection within 10 seconds
- **Transcription Accuracy**: Natural sentence formation with <5% fragmented sentences
- **Connection Reliability**: <1% connection failures after successful initial setup  
- **Debug Usage**: Debug toggle used by <10% of users (confirming it's not needed for normal operation)
- **Task Completion**: Users can complete voice conversations without needing manual controls

## Open Questions
1. **Sentence Timeout**: How long should the system wait before forcing sentence completion if no clear boundary is detected?
2. **Debug Persistence**: Should debug toggle state persist across page reloads or reset each time?
3. **Connection Timeout**: What's the appropriate timeout for initial connection attempts before showing error?
4. **Partial Transcription Delay**: Should there be a minimum delay before showing partial transcriptions to avoid flickering?
5. **Claude Response Integration**: Should Claude responses also use the same sentence-by-sentence streaming approach?

---

**Priority**: High  
**Target Timeline**: 2-3 weeks  
**Dependencies**: Existing voice gateway WebSocket infrastructure, Claude CLI integration  
**Risk Level**: Medium (requires coordination between frontend UX and backend sentence detection)