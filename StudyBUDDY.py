import sys
import threading
import asyncio
import pyaudio
import websockets
import json
import base64
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import QTimer
import os
from dotenv import load_dotenv
from Live_Transcription import DeepgramLiveTranscriber


#Window
class StudyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudyBUDDY Live Transcription")
        self.resize(1000, 800)
        layout = QVBoxLayout(self)

        #Mic volume to see if it's picking up anything
        self.mic_label = QLabel("Mic Volume: 0")
        layout.addWidget(self.mic_label)

        #Transcript
        self.transcript_text = QTextEdit(readOnly=True)
        self.transcript_text.setPlaceholderText("Transcript will show up here")
        self.transcript_text.setMinimumHeight(300)
        layout.addWidget(self.transcript_text)

        #Buttons
        self.load_button = self.create_button("Load Audio / Video", "#2196F3", "Select an audio or video file to transcribe.")
        layout.addWidget(self.load_button)

        self.start_button = self.create_button("▶ Start Live Transcription", "#4CAF50", "Begin live transcription using your microphone.")
        self.start_button.clicked.connect(self.start_transcription)
        layout.addWidget(self.start_button)

        self.stop_button = self.create_button("■ Stop Live Transcription", "#f44336", "Stop the ongoing live transcription.")
        self.stop_button.clicked.connect(self.stop_transcription)
        layout.addWidget(self.stop_button)

        self.save_audio_button = self.create_button("Save Audio", "#FF9800", "Save the recorded audio locally.")
        layout.addWidget(self.save_audio_button)

        self.summarize_button = self.create_button("Auto-Summarize Lecture", "#9C27B0", "Summarize transcript into key points.")
        layout.addWidget(self.summarize_button)

        self.flashcards_button = self.create_button("Generate Flashcards", "#3F51B5", "Generate Anki-ready flashcards.")
        layout.addWidget(self.flashcards_button)

        self.study_blocks_button = self.create_button("Create Study Blocks", "#795548", "Schedule study sessions in your calendar.")
        layout.addWidget(self.study_blocks_button)

        #Auto-summarize textbox
        self.summarize_text = QTextEdit()
        self.summarize_text.setPlaceholderText("Auto-summarized lecture will appear here")
        self.summarize_text.setMinimumHeight(150)
        layout.addWidget(self.summarize_text)

        #Generate flashcards textbox
        self.flashcards_text = QTextEdit()
        self.flashcards_text.setPlaceholderText("Generated flashcards will appear here")
        self.flashcards_text.setMinimumHeight(150)
        layout.addWidget(self.flashcards_text)

        self.transcriber = None
        self.transcriber_thread = None


    def create_button(self, text, color, tooltip):
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFont(QFont("Arial", 10, QFont.Bold))
        btn.setStyleSheet(f"""QPushButton {{background-color: {color};color: white;padding: 8px;border-radius: 5px;}}QPushButton:hover {{background-color: {self.lighten_color(color, 30)};}}""")
        btn.setMinimumHeight(40)
        return btn

    def lighten_color(self, hex_color, amount=30):
        hex_color = hex_color.lstrip("#")
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        r = min(r + amount, 255)
        g = min(g + amount, 255)
        b = min(b + amount, 255)
        return f"#{r:02x}{g:02x}{b:02x}"


    def update_gui(self, transcript=None, volume=None):
        if transcript:
            self.transcript_text.moveCursor(self.transcript_text.textCursor().End)
            self.transcript_text.insertPlainText(transcript + "\n")
            self.transcript_text.ensureCursorVisible()
        if volume is not None:
            self.mic_label.setText(f"Mic Volume: {int(volume)}")


    #Live transcription
    def start_transcription(self):
        if self.transcriber_thread and self.transcriber_thread.is_alive():
            return
        self.transcriber = DeepgramLiveTranscriber(self.update_gui)

        def run_transcriber():
            if sys.platform.startswith("win"):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.transcriber.transcribe())

        self.transcriber_thread = threading.Thread(target=run_transcriber, daemon=True)
        self.transcriber_thread.start()

    def stop_transcription(self):
        if self.transcriber:
            self.transcriber._stop_microphone()
            self.transcriber = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudyApp()
    window.show()
    sys.exit(app.exec())
