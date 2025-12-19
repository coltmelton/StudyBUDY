import asyncio
import inspect
import json
import os
from typing import Any, Dict, Iterable, Tuple

from dotenv import load_dotenv

try:
    import websockets
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "The `websockets` package is required for live transcription streaming. "
        "Install it with `pip install websockets` or via `pip install -r requirements.txt`."
    ) from exc

try:
    import pyaudio
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "PyAudio is required for live transcription. "
        "Install it with `pip install pyaudio` (see README for platform tips)."
    ) from exc

try:
    from deepgram import DeepgramClient
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "deepgram-sdk is required for live transcription. "
        "Install it with `pip install deepgram-sdk` or via `pip install -r requirements.txt`."
    ) from exc

load_dotenv()

# Runtime compatibility shim for websockets>=15 (additional_headers) vs older (extra_headers).
_CONNECT_SIGNATURE = inspect.signature(websockets.connect)
if "additional_headers" in _CONNECT_SIGNATURE.parameters:
    _HANDSHAKE_HEADER_KEY = "additional_headers"
else:
    _HANDSHAKE_HEADER_KEY = "extra_headers"

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


class DeepgramLiveTranscriber:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is not configured. "
                "Add it to your environment or .env file before starting live transcription."
            )

        # Initialising the SDK client keeps parity with Deepgram's examples and allows future re-use.
        self.dg = DeepgramClient(api_key=self.api_key)
        self.ws = None
        self.p = None
        self.stream = None
        self.loop: asyncio.AbstractEventLoop | None = None

    async def transcribe(self):
        url = "wss://api.deepgram.com/v1/listen?punctuate=true&language=en"
        connect_kwargs = self._build_connect_kwargs()

        async with websockets.connect(url, **connect_kwargs) as ws:
            self.ws = ws
            self._start_microphone()
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    if "channel" in data and "alternatives" in data["channel"]:
                        transcript = data["channel"]["alternatives"][0].get("transcript", "")
                        if transcript:
                            print("Live:", transcript)
            finally:
                self._stop_microphone()

    def _build_connect_kwargs(self) -> Dict[str, Any]:
        handshake_headers: Iterable[Tuple[str, str]] = [("Authorization", f"Token {self.api_key}")]
        if _HANDSHAKE_HEADER_KEY == "additional_headers":
            return {"additional_headers": handshake_headers}
        return {"extra_headers": handshake_headers}

    def _start_microphone(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self._callback,
        )
        self.stream.start_stream()

    def _stop_microphone(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        if self.p is not None:
            self.p.terminate()
            self.p = None

    def _callback(self, in_data, *_):
        if not self.ws or not self.loop or self.loop.is_closed():
            return (in_data, pyaudio.paAbort)

        send_coro = self.ws.send(in_data)
        asyncio.run_coroutine_threadsafe(send_coro, self.loop)
        return (in_data, pyaudio.paContinue)

    def start(self):
        self.loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.transcribe())
        finally:
            asyncio.set_event_loop(None)
            if self.stream and self.stream.is_active():
                self.stream.stop_stream()
            if self.stream:
                self.stream.close()
            if self.p:
                self.p.terminate()
            if self.loop.is_running():
                self.loop.stop()
            self.loop.close()
            self.loop = None
