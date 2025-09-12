import os
import whisper


#Find and run ffmpeg from current directory. Used for decoding and handling audio files
ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg", "ffmpeg.exe")
ffmpeg_dir = os.path.dirname(ffmpeg_path)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")


class FileTranscriber:
    def __init__(self, update_callback=None, model_size="base", language="en"):

        self.model = whisper.load_model(model_size)
        self.language = language
        self.update_callback = update_callback

    def transcribe(self, file_path: str) -> str:
        normalized_path = os.path.normpath(file_path)

        if not os.path.exists(normalized_path):
            return

        #Only allow files that are .wav to appear
        if not normalized_path.lower().endswith(".wav"):
            return

        try:
            result = self.model.transcribe(normalized_path, language=self.language)
            text = result.get("text", "").strip()

            if text and self.update_callback:
                self.update_callback(text)

            return text

        except Exception:
            return ""
