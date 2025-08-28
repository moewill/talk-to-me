#!/usr/bin/env python3
"""
🎤 Voice-Driven Claude CLI - Production Startup Script

This script starts the complete voice automation system for production use.

Usage:
    python start_system.py              # Start on default port 8080
    python start_system.py --port 8081  # Start on custom port

Features:
- WebSocket server for voice commands
- Real-time audio processing with Whisper
- Intent classification for Claude commands  
- Automatic Claude CLI execution
- Comprehensive error handling and logging
"""

import sys
sys.path.append('src')

import asyncio
import argparse
import signal
import logging
from voice_gateway import VoiceGateway

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceClaudeServer:
    """Production server for Voice-Driven Claude CLI system."""
    
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.gateway = None
        self.running = False
        
    async def start(self):
        """Start the voice processing server."""
        try:
            print("🎤 VOICE-DRIVEN CLAUDE CLI - PRODUCTION SERVER")
            print("=" * 60)
            print(f"Starting server on {self.host}:{self.port}")
            print("Features enabled:")
            print("  • Real-time voice processing ✅")
            print("  • Claude command detection ✅")
            print("  • Automatic CLI execution ✅")
            print("  • WebSocket API ✅")
            print()
            
            # Initialize gateway
            self.gateway = VoiceGateway(host=self.host, port=self.port)
            
            # Start server
            await self.gateway.start_server()
            
            if self.gateway.running:
                self.running = True
                print(f"🚀 Server started successfully!")
                print(f"   WebSocket URL: ws://{self.host}:{self.port}/voice")
                print(f"   Ready to process voice commands...")
                print()
                print("💡 Example usage:")
                print('   Connect via WebSocket and send:')
                print('   {"type": "audio", "data": "base64_encoded_audio"}')
                print()
                print("Press Ctrl+C to stop the server")
                print()
                
                # Keep server running
                try:
                    while self.running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Shutdown requested...")
                    
            else:
                print("❌ Failed to start server")
                return False
                
        except Exception as e:
            print(f"❌ Server error: {e}")
            logger.error(f"Server startup failed: {e}")
            return False
        finally:
            await self.stop()
            
        return True
    
    async def stop(self):
        """Stop the server gracefully."""
        if self.gateway and self.gateway.running:
            print("🔄 Stopping server...")
            await self.gateway.stop_server()
            print("✅ Server stopped successfully")
        
        self.running = False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def run_server(host, port):
    """Run the production server."""
    server = VoiceClaudeServer(host=host, port=port)
    server.setup_signal_handlers()
    
    try:
        success = await server.start()
        return success
    except KeyboardInterrupt:
        print("\n👋 Server interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ Server failed: {e}")
        return False

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Voice-Driven Claude CLI Production Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_system.py                    # Start on localhost:8080
  python start_system.py --port 8081       # Custom port
  python start_system.py --host 0.0.0.0    # Listen on all interfaces
        """
    )
    
    parser.add_argument(
        '--host', 
        default='localhost',
        help='Host to bind the server (default: localhost)'
    )
    
    parser.add_argument(
        '--port', 
        type=int,
        default=8080,
        help='Port to bind the server (default: 8080)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demonstration instead of starting server'
    )
    
    args = parser.parse_args()
    
    if args.demo:
        print("🎭 Running demonstration instead of starting server...")
        import subprocess
        result = subprocess.run([sys.executable, 'FINAL_DEMO.py'])
        return result.returncode
    
    # Start the production server
    try:
        success = asyncio.run(run_server(args.host, args.port))
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)