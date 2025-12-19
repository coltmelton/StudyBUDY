StudyBUDY combines speech-to-text transcription with AI-powered note taking and study guidance.

## Features
- Upload audio or video for high-quality Whisper transcription.
- Turn transcripts into structured, topic-oriented notes.
- Replace flashcard generation with an actionable study plan generator.
- Launch the StudyBUDY PySide desktop client or interact with the new FastAPI backend and web playground.
- Optional live transcription powered by Deepgram's realtime streaming API.

## Getting Started
1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` (see below) and add the API keys you intend to use.

### Environment Variables
Add any of the following to `.env` or your shell:
- `OPENAI_API_KEY` (required for Whisper transcription and OpenAI text generation)
- `OPENAI_COMPLETION_MODEL` (optional, defaults to `gpt-4o-mini`)
- `OPENAI_TRANSCRIPTION_MODEL` (optional, defaults to `whisper-1`)
- `GROQ_API_KEY` (optional alternative for LLaMA models, defaults to `llama-3.1-8b-instant`)
- `GROQ_MODEL` (optional override for the Groq model)
- `DEEPGRAM_API_KEY` (required only for live transcription)
- `CORS_ALLOW_ORIGINS` (comma-separated origins for the API, defaults to `*`)
- `OPENAI_REQUEST_TIMEOUT`, `LLM_REQUEST_TIMEOUT` (optional timeouts in seconds)

### Running the API
```
uvicorn api_server:app --reload
```
- Swagger/Redoc documentation: `http://localhost:8000/docs`
- Built-in GUI playground: `http://localhost:8000/`

### Running the Desktop App
```
python StudyBUDY.py
```
Use the buttons to load media, view generated notes, and review the study plan.
- If you encounter `ModuleNotFoundError: No module named 'PySide6'`, install the Qt bindings with `pip install PySide6`.
- Live transcription depends on `pyaudio`, `websockets`, and `deepgram-sdk`. Windows users may prefer the pre-built wheels linked at https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio.

### Live Transcription (optional)
```
python Live_Transcription.py
```
Requires a working microphone and a valid `DEEPGRAM_API_KEY`.

## Repository Layout
- `api_server.py` (FastAPI application exposing transcription, notes, and study plan endpoints)
- `static/index.html` (web GUI for testing the API end-to-end)
- `AudioVideoTranscribe.py` (Whisper helper functions)
- `llamaLLM_Interface.py` (provider-agnostic language model helpers)
- `StudyBUDY.py` (PySide6 desktop client)
- `Live_Transcription.py` (Deepgram live transcription script)
- `requirements.txt` (project dependencies)

## Next Steps
- Configure production deployment (reverse proxy, HTTPS, auth).
- Persist transcripts and generated artefacts using a database if needed.
