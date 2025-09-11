#WhisperLiveTranscriber.py
import threading
import queue
import numpy as np
import sounddevice as sd
import whisper
import time
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
        self.chunk_size = 1024
        self.buffer = np.zeros((0,), dtype=np.float32)
        self.paragraph_buffer = ""
        self.last_emitted_text = ""


        self.voice_level = 0.005
        self.pause_trigger_detection = 0.9
        self.max_pause = 1.5
        self.min_speech_time = 0.9
        self.max_speech_time = 15.0
        self.last_time_talked = time.time()
        self.start_talking_time = None
        self.transcript_history = ""

        self.volume_signal.connect(lambda v: self.update_callback(volume=v))
        self.transcript_signal.connect(lambda t: self.update_callback(transcript=t))

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(status)
        samples = indata[:, 0] if indata.ndim > 1 else indata
        rms = np.sqrt(np.mean(np.square(samples)))
        if rms < self.voice_level:
            #Detect and display live volume meter
            self.volume_signal.emit(min(int(rms * 20000), 9999))
            return

        #track the last time speech has been detected
        currently_speaking = time.time()
        self.last_time_talked = currently_speaking
        if self.start_talking_time is None:
            self.start_talking_time = currently_speaking

        self.audio_queue.put(samples.copy())
        self.volume_signal.emit(min(int(rms * 20000), 9999))


    def _clean_text(self, text):
        text = text.strip()
        #Remove Whisper AI endings
        endings = ["thank you", "thanks", "thank you."]
        for ending in endings:
            if text.lower().endswith(ending):
                text = text[:-len(ending)].strip()

        #Remove continual repeated words
        words = text.split()
        new_words = []
        prev_word = None
        for word in words:
            if word != prev_word:
                new_words.append(word)
            prev_word = word
        return " ".join(new_words)


    #Transition smoothly between sentences if needed
    def _context_prompt(self, max_chars=200):
        tail = self.transcript_history[-max_chars:].strip()
        return tail if tail else None


    def _determine_end_of_sentence(self):

        #Don't do anything if the user isn't talking
        if self.start_talking_time is None:
            return False

        #Begin timing and length
        now = time.time()
        since_voice = now - self.last_time_talked
        utterance_len = len(self.buffer) / float(self.samplerate)


        #Detect if user has finished a sentence with a pause
        if utterance_len >= self.min_speech_time and since_voice >= self.pause_trigger_detection:
            return True

        #Detect if there's a long pause after an extremely short sentence
        if utterance_len > 0 and since_voice >= self.max_pause:
            return True

        #Return if the speech is too long without any pauses
        if utterance_len >= self.max_speech_time:
            return True

        return False


    #Collect chunks and send to buffer
    def _collect_chunks(self):
        got_any = False
        while True:
            try:
                chunk = self.audio_queue.get_nowait()
                self.buffer = np.concatenate([self.buffer, chunk])
                got_any = True
            except queue.Empty:
                break
        return got_any



    def _convert_and_send(self):
        #Fix no audio error
        if len(self.buffer) == 0:
            return

        #Fit audio to whisper's liking
        audio = whisper.pad_or_trim(self.buffer)

        #Key word arguments providing last few words for predicting the upcoming words accurately
        kwargs = dict(language="en")
        prompt = self._context_prompt()
        if prompt:
            kwargs["prompt"] = prompt
        #Fix the raw data
        result = self.model.transcribe(audio, **kwargs)
        text = result.get("text", "").strip()
        text = self._clean_text(text)

        #Check for duplications and send text
        if text and text != self.last_emitted_text:
            self.transcript_signal.emit(text)
            self.last_emitted_text = text
            self.transcript_history = (self.transcript_history + " " + text).strip()

        #Reset
        self.buffer = np.zeros((0,), dtype=np.float32)
        self.start_talking_time = None


    def _transcribe_loop(self):
        while self.running:
            #Collect chunks
            got_audio = self._collect_chunks()

            # Decide whether to finalize the speech
            if self._determine_end_of_sentence():
                self._convert_and_send()


            #Double check and grab audio if waiting too long
            if not got_audio:
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.05)
                    self.buffer = np.concatenate([self.buffer, audio_chunk])
                except queue.Empty:
                    pass


    def start(self):
        self.running = True
        self.stream = sd.InputStream(samplerate=self.samplerate,channels=1,dtype="float32",blocksize=self.chunk_size,callback=self._callback)
        self.stream.start()
        threading.Thread(target=self._transcribe_loop, daemon=True).start()

    def stop(self):
        self.running = False
        if hasattr(self, "stream"):
            self.stream.stop()
            self.stream.close()
