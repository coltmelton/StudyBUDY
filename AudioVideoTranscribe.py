import os
import requests

def transcribe_with_whisper(file_path: str, api_key: str) -> str:
    """
    Transcribe a file using OpenAI Whisper API.
    """
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(file_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(file_path), audio_file),
            "model": (None, "whisper-1"),
        }
        res = requests.post(url, headers=headers, files=files)
        res.raise_for_status()
        return res.json().get("text", "")
