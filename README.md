StudyBUDDY
 - StudyBUDDY is a Python based application for live and pre-recorded lecture transcription, automated summarization, flashcard generation, and study block scheduling. It integrates Whisper for transcription, Ollama for summarization, and AnkiConnect for flashcards.


FEATURES
- Load Audio / Video: Transcribe .wav audio files from pre-recorded lectures.
- Start and Stop Live Transcription: Capture speech from your microphone in real-time.
- Save Transcript: Store transcript as a .txt file in local file explorer.
- Auto-Summarize: Generate concise, structured lecture summaries.
- Generate Flashcards: Automatically create Anki-ready flashcards from summaries or personal Q&As.
- Study Block Scheduling: Create study sessions in .ics format for Google Calendar import.


REQUIREMENTS
- Python 3.10 or higher
- PySide6
- Whisper
- sounddevice
- ics
- All other required Python libraries not explicitly mentioned in this README can be installed via pip
- Note: On Windows, you need ffmpeg placed in the ffmpeg folder next to FileTranscriber.py
- Anki installed with AnkiConnect plugin locally (required for flashcard generation): https://ankiweb.net/shared/info/2055492159
- Ollama installed and running locally for summarization: https://ollama.com/
Recommended model: https://ollama.com/library/llama3:8b


Running StudyBUDDY
- python StudyBUDDY.py
    - Load Audio/Video: Transcribe .wav files.
    - Start Live Transcription: Use your microphone to capture live speech.
    - Stop Live Transcription: Stop recording.
    - Save Transcript: Save transcription as a .txt file.
    - Auto-Summarize Lecture: Summarize the transcript via Ollama (ensure this is running upon using).
    - Generate Flashcards: Push suggested flashcards to Anki (have this app opened upon using).
    - Create Study Blocks: Schedule study sessions and export .ics files to Google Calendar.
