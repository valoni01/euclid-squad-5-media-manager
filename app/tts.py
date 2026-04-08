import tempfile
from pathlib import Path

from openai import AsyncOpenAI

MAX_TTS_CHARS = 4096

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


async def text_to_speech(
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
) -> str:
    """Convert *text* to an MP3 file and return the file path.

    Long texts are truncated to the API limit so we never send an
    oversized payload.
    """
    if not text or not text.strip():
        return ""

    truncated = text[:MAX_TTS_CHARS]
    client = _get_client()
    response = await client.audio.speech.create(
        model=model,
        voice=voice,
        input=truncated,
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    Path(tmp.name).write_bytes(response.content)
    return tmp.name
