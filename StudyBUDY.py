import os
import sys
from dotenv import load_dotenv

try:
    from PySide6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QPushButton,
        QTextEdit,
        QFileDialog,
        QLabel,
        QMessageBox,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "PySide6 is required for the StudyBUDY desktop client. "
        "Install it with `pip install PySide6` or `pip install -r requirements.txt`."
    ) from exc

from AudioVideoTranscribe import transcribe_with_whisper
from llamaLLM_Interface import generate_structured_notes, generate_study_plan

load_dotenv()

class StudyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudyBUDY")
        self.resize(800, 600)

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

        self.study_plan_text = QTextEdit(readOnly=True)
        self.layout.addWidget(self.study_plan_text)

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
            transcript = transcribe_with_whisper(file_path)
            self.transcript_text.setPlainText(transcript)
            self.process_notes(transcript)
            self.build_study_plan(transcript)
        except Exception as e:
            self.transcript_text.setPlainText(f"Error: {e}")

    def process_notes(self, transcript: str):
        self.notes_text.setPlainText("Generating notes...")
        try:
            notes = generate_structured_notes(transcript)
            self.notes_text.setPlainText(notes)
        except Exception as e:
            self.notes_text.setPlainText(f"Error: {e}")

    def build_study_plan(self, transcript: str):
        self.study_plan_text.setPlainText("Building study plan...")
        try:
            plan = generate_study_plan(transcript)
            self.study_plan_text.setPlainText(plan)
        except Exception as e:
            self.study_plan_text.setPlainText(f"Error: {e}")

    def start_live_transcription(self):
        try:
            from Live_Transcription import DeepgramLiveTranscriber
        except ImportError as exc:
            QMessageBox.warning(
                self,
                "Dependency Missing",
                "Live transcription is unavailable because an optional dependency failed to import.\n\n"
                f"{exc}",
            )
            return

        try:
            transcriber = DeepgramLiveTranscriber()
            transcriber.start()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Live Transcription Error",
                "Unable to start live transcription.\n\n"
                f"{exc}",
            )

def main():
    app = QApplication(sys.argv)
    win = StudyApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
