import os
from io import BytesIO
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"
DEFAULT_TRANSCRIPTION_MODEL = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")


class TranscriptionError(RuntimeError):
    """Raised when the transcription API returns an error."""


def _require_openai_api_key(explicit_key: Optional[str] = None) -> str:
    api_key = explicit_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise TranscriptionError(
            "Missing OpenAI API key. Set OPENAI_API_KEY in the environment or .env file."
        )
    return api_key


def _dispatch_transcription(
    file_name: str,
    file_payload,
    api_key: str,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {
        "file": (file_name, file_payload),
        "model": (None, DEFAULT_TRANSCRIPTION_MODEL),
        "response_format": (None, "text"),
    }

    timeout = int(os.getenv("OPENAI_REQUEST_TIMEOUT", "300"))
    response = requests.post(
        OPENAI_TRANSCRIPTION_URL,
        headers=headers,
        files=files,
        timeout=timeout,
    )

    if response.status_code >= 400:
        raise TranscriptionError(
            f"OpenAI transcription failed ({response.status_code}): {response.text}"
        )

    return response.text.strip()


def transcribe_with_whisper(file_path: str, api_key: Optional[str] = None) -> str:
    """
    Transcribe a local media file using the OpenAI Whisper REST API.
    """
    resolved_key = _require_openai_api_key(api_key)
    with open(file_path, "rb") as audio_file:
        return _dispatch_transcription(os.path.basename(file_path), audio_file, resolved_key)


def transcribe_bytes(
    file_name: str,
    payload: bytes,
    api_key: Optional[str] = None,
) -> str:
    """
    Transcribe an in-memory media object, e.g. from an uploaded file.
    """
    buffer = BytesIO(payload)
    buffer.seek(0)
    resolved_key = _require_openai_api_key(api_key)
    return _dispatch_transcription(file_name, buffer, resolved_key)
