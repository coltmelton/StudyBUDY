import asyncio
import websockets
import json
import pyaudio
from deepgram import Deepgram
import os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class DeepgramLiveTranscriber:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.dg = Deepgram(self.api_key)
        self.ws = None
        self.p = None
        self.stream = None

    async def transcribe(self):
        url = "wss://api.deepgram.com/v1/listen?punctuate=true&language=en"
        async with websockets.connect(url, extra_headers={"Authorization": f"Token {self.api_key}"}) as ws:
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

    def _start_microphone(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                                  frames_per_buffer=CHUNK, stream_callback=self._callback)
        self.stream.start_stream()

    def _stop_microphone(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def _callback(self, in_data, *_):
        asyncio.run_coroutine_threadsafe(self.ws.send(in_data), asyncio.get_event_loop())
        return (in_data, pyaudio.paContinue)

    def start(self):
        asyncio.get_event_loop().run_until_complete(self.transcribe())
