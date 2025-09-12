import sys
import threading
import asyncio
import pyaudio
import websockets
import json
import base64
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QFileDialog
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import QTimer, QMetaObject, Qt
import os
from WhisperLiveTranscriber import WhisperLiveTranscriber
from ollama_SummarizeText import SummarizeText

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
        self.transcript_text = QTextEdit(readOnly=False)
        self.transcript_text.setPlaceholderText("Transcript will show up here")
        self.transcript_text.setMinimumHeight(300)
        layout.addWidget(self.transcript_text)

        #Buttons
        self.load_button = self.create_button("Load Audio / Video", "#2196F3", "Select an audio or video file to transcribe.")
        self.load_button.clicked.connect(self.load_audio_video)
        layout.addWidget(self.load_button)

        self.start_button = self.create_button("Start Live Transcription", "#4CAF50", "Begin live transcription using your microphone.")
        self.start_button.clicked.connect(self.start_transcription)
        layout.addWidget(self.start_button)

        self.stop_button = self.create_button("Stop Live Transcription", "#f44336", "Stop the ongoing live transcription.")
        self.stop_button.clicked.connect(self.stop_transcription)
        layout.addWidget(self.stop_button)

        self.save_audio_button = self.create_button("Save Transcript", "#FF9800", "Save the recorded audio locally.")
        self.save_audio_button.clicked.connect(self.save_transcription)
        layout.addWidget(self.save_audio_button)

        self.summarize_button = self.create_button("Auto-Summarize Lecture", "#9C27B0", "Summarize transcript into key points.")
        self.summarizer = SummarizeText(model="llama3:8b")
        self.summarize_button.clicked.connect(self.auto_summarize)
        layout.addWidget(self.summarize_button)

        self.flashcards_button = self.create_button("Generate Flashcards", "#3F51B5", "Generate Anki-ready flashcards.")
        self.flashcards_button.clicked.connect(self.generate_flashcards)
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
        self.flashcards_text.setPlaceholderText("Suggested flashcards are provided from the auto-summarization, but you're free to create your own.\n" \
        "Please format your flashcards like this:\n" \
        "Q: What is 2+2?\n" \
        "A: 4\n" \
        "Q: What is the largest state in the United States?\n" \
        "A: Alaska\n")
        self.flashcards_text.setMinimumHeight(150)
        layout.addWidget(self.flashcards_text)

        self.transcriber = None
        self.transcriber_thread = None

    def create_button(self, text, color, tooltip):
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setFont(QFont("Arial", 10, QFont.Bold))
        button.setStyleSheet(f"""QPushButton {{background-color: {color};color: white;padding: 8px;border-radius: 5px;}}QPushButton:hover {{background-color: {self.lighten_color(color, 30)};}}""")
        button.setMinimumHeight(40)

        #Highlight button
        button.clicked.connect(self.make_highlight_button(button))

        return button

    def make_highlight_button(self, button):
        """Return a function that highlights this specific button when clicked."""
        def handler():
            self.highlight_button(button)
        return handler

    def lighten_color(self, hex_color, amount=30):
        hex_color = hex_color.lstrip("#")
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        r = min(r + amount, 255)
        g = min(g + amount, 255)
        b = min(b + amount, 255)
        return f"#{r:02x}{g:02x}{b:02x}"


    def highlight_button(self, active_button):
        #Reset all buttons to their original colors
        buttons = [
            (self.start_button, "#4CAF50"),
            (self.stop_button, "#f44336"),
            (self.load_button, "#2196F3"),
            (self.save_audio_button, "#FF9800"),
            (self.summarize_button, "#9C27B0"),
            (self.flashcards_button, "#3F51B5"),
            (self.study_blocks_button, "#795548"),
        ]

        for button, color in buttons:
            button.setStyleSheet(f"""QPushButton {{background-color: {color};color: white;padding: 8px;border-radius: 5px;}}QPushButton:hover {{background-color: {self.lighten_color(color, 30)};}}""")

        #Yellow highlight to active button
        if active_button:
            active_button.setStyleSheet(active_button.styleSheet() + " QPushButton { border: 3px solid yellow; }")


    #Fill in the transcript box
    def update_gui(self, transcript=None, volume=None):
        #Only add non-empty lines
        if transcript is not None:
            if transcript.strip():  #Only add non-empty lines
                self.transcript_text.moveCursor(QTextCursor.End)
                self.transcript_text.insertPlainText(transcript + "\n")
                self.transcript_text.ensureCursorVisible()
        if volume is not None:
            display_volume = min(int(volume * 10), 9999)
            self.mic_label.setText(f"Mic Volume: {display_volume}")


    #Start transcription button functionality
    def start_transcription(self):
        if self.transcriber_thread and self.transcriber_thread.is_alive():
            return
        self.transcriber = WhisperLiveTranscriber(self.update_gui, model_size="base")
        self.transcriber_thread = threading.Thread(target=self.transcriber.start, daemon=True)
        self.transcriber_thread.start()

    # transcription button functionality
    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.stop()
            self.transcriber = None

    #Save audio functionality
    def save_transcription(self):
        transcript = self.transcript_text.toPlainText()

        #If there's no transcript, don't allow a save
        if not transcript.strip():
            print("No Transcript to save.")
            return

        #Let the user choose the file path
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Transcript", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(transcript)
                print(f"Transcript saved to {file_path}")
            except IOError as e:
                print(f"Error saving file: {e}")


    #Load file to be transcribed
    def load_audio_video(self):
        #Only transcribe .wav files
        file_path, file_filter = QFileDialog.getOpenFileName(self,"Select Audio/Video File","","Wav Files (*.wav)")

        if not file_path:
            return

        if not file_path.lower().endswith(".wav"):
            print("Error: Please select a valid .wav file.")
            return

        if not os.path.exists(file_path):
            print("Error: File does not exist.")
            return

        #Import transcribe files class
        from FileTranscriber import FileTranscriber


        #Insert the text to the box
        def gui_update(text):
            self.transcript_text.moveCursor(QTextCursor.End)
            self.transcript_text.insertPlainText(text + "\n")
            self.transcript_text.ensureCursorVisible()

        print("Uploading audio file...")

        transcriber = FileTranscriber(update_callback=gui_update, model_size="base")

        #Transcribe the file
        transcriber.transcribe(file_path)
        print("Audio file uploaded successfully.")


    #Auto summarize transcripts
    def auto_summarize(self):
        transcript = self.transcript_text.toPlainText()
        if not transcript.strip():
            self.summarize_text.setPlainText("No transcript available to summarize.")
            return

        self.summarize_text.setPlainText("Summarizing... please wait.")

        #Disable the button to prevent multiple requests
        self.summarize_button.setEnabled(False)

        # store results in instance variables for thread communication
        self.summary_result = None
        self.summary_success = False


        def run_in_thread():
            try:
                print(f"Starting summarization...")
                summary = self.summarizer.summarize(transcript)
                print(f"Summarization complete.")

                #store results in instance variables
                self.summary_result = summary
                self.summary_success = True
            except Exception as e:
                error_msg = f"Error during summarization: {str(e)}"
                print(error_msg)
                self.summary_result = error_msg
                self.summary_success = False

        #Start thread
        threading.Thread(target=run_in_thread, daemon=True).start()

        #QTimer to check for completion periodically
        self.summary_check_timer = QTimer()
        self.summary_check_timer.timeout.connect(self.check_summary_complete)
        #Check every 100ms
        self.summary_check_timer.start(100)


    def check_summary_complete(self):
        if self.summary_result is not None:
            #Stop the timer
            self.summary_check_timer.stop()

            #Update the GUI with the result
            self.actually_update_summary(self.summary_result, self.summary_success)

            self.summary_result = None


    #Update gui and reset everything
    def actually_update_summary(self, result, success=True):

        self.summarize_text.setPlainText(result)
        self.summarize_button.setEnabled(True)
        self.summarize_button.setText("Auto-Summarize Lecture")

        if success:
            print("Summary updated successfully in GUI")
        else:
            print("Error message updated in GUI")


    def generate_flashcards(self):
        from anki_GenerateFlashcards import GenerateFlashcards
        anki = GenerateFlashcards()

        flashcards_text = self.flashcards_text.toPlainText()
        if not flashcards_text.strip():
            print("No flashcards available to push.")
            return

        try:
            anki.create_deck("StudyBuddy Deck")
            result = anki.add_flashcards(flashcards_text, deck_name="StudyBuddy Deck")
            print("Flashcards pushed to Anki:", result)
        except Exception as e:
            print(f"Error pushing to Anki: {e}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudyApp()
    window.show()
    sys.exit(app.exec())
