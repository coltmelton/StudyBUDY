import os
import json
import asyncio
import pyaudio
import websockets
import base64
import numpy as np
from dotenv import load_dotenv
from PySide6.QtCore import QTimer

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class DeepgramLiveTranscriber:
    def __init__(self, update_callback):
        self.api_key = DEEPGRAM_API_KEY
        self.update_callback = update_callback
        self.ws = None
        self.p = None
        self.stream = None
        self.loop = None
        self.running = False

    async def transcribe(self):
        url = f"wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000&punctuate=true&language=en"
        headers = [("Authorization", f"Token {self.api_key}")]
        self.loop = asyncio.get_running_loop()
        self.running = True

        async with websockets.connect(url, extra_headers=headers) as ws:
            self.ws = ws
            self._start_microphone()
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    if "channel" in data and "alternatives" in data["channel"]:
                        transcript = data["channel"]["alternatives"][0].get("transcript", "")
                        if transcript:
                            QTimer.singleShot(0, lambda t=transcript: self.update_callback(transcript=t))
            finally:
                self._stop_microphone()

    def _start_microphone(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        import threading
        threading.Thread(target=self._read_mic_loop, daemon=True).start()

    def _read_mic_loop(self):
        while self.running and self.ws:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                encoded = base64.b64encode(data).decode("utf-8")
                payload = json.dumps({"audio": encoded})
                asyncio.run_coroutine_threadsafe(self.ws.send(payload), self.loop)
                volume = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
                QTimer.singleShot(0, lambda v=volume: self.update_callback(volume=v))
            except Exception as e:
                print("Mic read error:", e)

    def _stop_microphone(self):
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
