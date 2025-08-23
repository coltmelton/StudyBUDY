#WhisperLiveTranscriber.py
import threading
import queue
import numpy as np
import sounddevice as sd
import whisper
from PySide6.QtCore import QObject, Signal


class WhisperLiveTranscriber(QObject):
    volume_signal = Signal(int)
    transcript_signal = Signal(str)

    def __init__(self, update_callback, model_size="base"):
        super().__init__()
        self.update_callback = update_callback
        self.model = whisper.load_model(model_size)
        self.running = False
        self.audio_queue = queue.Queue()
        self.samplerate = 16000
        self.buffer = np.zeros((0,), dtype=np.float32)

        #Connect signals to GUI callback
        self.volume_signal.connect(lambda v: self.update_callback(volume=v))
        self.transcript_signal.connect(lambda t: self.update_callback(transcript=t))



    #Start microphone input stream
    def start(self):
        self.running = True
        self.stream = sd.InputStream(samplerate=self.samplerate,channels=1,dtype="float32",callback=self._callback)
        self.stream.start()

        #Transcription thread
        threading.Thread(target=self._transcribe_loop, daemon=True).start()




    def _callback(self, indata, frames, time, status):
        if status:
            print(status)

        samples = indata[:, 0] if indata.ndim > 1 else indata
        self.audio_queue.put(samples.copy())

        # Compute RMS volume
        rms = np.sqrt(np.mean(np.square(samples)))
        display_volume = min(int(rms * 20000), 9999)
        self.volume_signal.emit(display_volume)

    def _transcribe_loop(self):
        while self.running:
            try:
                chunk = self.audio_queue.get(timeout=0.5)
                self.buffer = np.concatenate([self.buffer, chunk])

                #Transcribe every 2 seconds of audio for more live updates
                if len(self.buffer) >= self.samplerate * 2:
                    audio = whisper.pad_or_trim(self.buffer)
                    result = self.model.transcribe(audio, language="en")
                    text = result.get("text", "").strip()


                    #Emit transcript signal
                    self.transcript_signal.emit(text)

                    #Reset buffer
                    self.buffer = np.zeros((0,), dtype=np.float32)
            except queue.Empty:
                continue




    def stop(self):
        self.running = False
        if hasattr(self, "stream"):
            self.stream.stop()
            self.stream.close()
