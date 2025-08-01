import os
import sys
import AudioVideoTranscribe
import llamaLLM_Interface
import Live_Transcription

from dotenv import load_dotenv

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel
)
from AudioVideoTranscribe import transcribe_with_whisper
from llamaLLM_Interface import call_llama
from Live_Transcription import DeepgramLiveTranscriber

load_dotenv()

class StudyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudyBUDY")
        self.resize(800, 600)

        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Load audio or video")
        self.layout.addWidget(self.label)

        self.load_button = QPushButton("Load Audio / Video")
        self.load_button.clicked.connect(self.import_media)
        self.layout.addWidget(self.load_button)

        self.transcript_text = QTextEdit(readOnly=True)
        self.layout.addWidget(self.transcript_text)

        self.notes_text = QTextEdit(readOnly=True)
        self.layout.addWidget(self.notes_text)

        self.quiz_text = QTextEdit(readOnly=True)
        self.layout.addWidget(self.quiz_text)

        self.live_button = QPushButton("Start Live Transcription")
        self.live_button.clicked.connect(self.start_live_transcription)
        self.layout.addWidget(self.live_button)

    def import_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio/Video File",
            filter="Audio/Video Files (*.mp3 *.wav *.m4a *.mp4 *.mov *.avi)"
        )
        if file_path:
            self.label.setText(f"Selected: {os.path.basename(file_path)}")
            self.transcribe_file(file_path)

    def transcribe_file(self, file_path):
        self.transcript_text.setPlainText("Transcribing with Whisper API...")
        try:
            transcript = transcribe_with_whisper(file_path, self.openai_api_key)
            self.transcript_text.setPlainText(transcript)
            self.process_notes(transcript)
            self.generate_quiz(transcript)
        except Exception as e:
            self.transcript_text.setPlainText(f"Error: {e}")

    def process_notes(self, transcript: str):
        self.notes_text.setPlainText("Generating notes...")
        prompt = f"Convert the following into clear, structured notes:\n\n{transcript}"
        try:
            notes = call_llama(prompt)
            self.notes_text.setPlainText(notes)
        except Exception as e:
            self.notes_text.setPlainText(f"Error: {e}")

    def generate_quiz(self, transcript: str):
        self.quiz_text.setPlainText("Generating quiz...")
        prompt = f"Create 5 quiz questions based on the following:\n\n{transcript}"
        try:
            quiz = call_llama(prompt)
            self.quiz_text.setPlainText(quiz)
        except Exception as e:
            self.quiz_text.setPlainText(f"Error: {e}")

    def start_live_transcription(self):
        transcriber = DeepgramLiveTranscriber()
        transcriber.start()

def main():
    app = QApplication(sys.argv)
    win = StudyApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
