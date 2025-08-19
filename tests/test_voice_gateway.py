import pytest
import asyncio
from src.voice_gateway import VoiceGateway


@pytest.fixture
def voice_gateway():
    return VoiceGateway()


def test_voice_gateway_initialization(voice_gateway):
    assert voice_gateway is not None
    assert voice_gateway.claude_cli_path == "claude"


# TODO: Add more comprehensive tests for audio processing,
# intent detection, and Claude CLI integration
