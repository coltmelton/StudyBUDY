import os
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from PyPDF2 import PdfReader
from docx import Document
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)
from AudioVideoTranscribe import TranscriptionError, transcribe_bytes
from llamaLLM_Interface import (
    LanguageModelError,
    generate_structured_notes,
    generate_study_plan,
    generate_quiz,
)

load_dotenv()

app = FastAPI(
    title="StudyBUDY API",
    version="0.2.0",
    description=(
        "REST API for StudyBUDY workflows: upload audio/video for transcription, "
        "generate notes, and build an actionable study plan."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscriptPayload(BaseModel):
    transcript: str


class LinkPayload(BaseModel):
    url: str


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Lightweight endpoint to verify that the API is running.
    """
    return {"status": "ok"}


@app.post("/transcriptions")
async def transcribe_media(file: UploadFile = File(...)) -> dict[str, str]:
    """
    Accepts an uploaded media file and returns the Whisper transcription text.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_name = file.filename or "upload"

    try:
        transcript = transcribe_bytes(file_name, content)
    except TranscriptionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"transcript": transcript}


@app.post("/notes")
def create_notes(payload: TranscriptPayload) -> dict[str, str]:
    """
    Transform a raw transcript into structured study notes.
    """
    _guard_payload(payload.transcript)

    try:
        notes = generate_structured_notes(payload.transcript)
    except LanguageModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"notes": notes}


@app.post("/study-plan")
def create_study_plan(payload: TranscriptPayload) -> dict[str, str]:
    """
    Generate an actionable study plan from the provided transcript.
    """
    _guard_payload(payload.transcript)

    try:
        plan = generate_study_plan(payload.transcript)
    except LanguageModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"study_plan": plan}


@app.post("/quiz")
def create_quiz(payload: TranscriptPayload) -> dict[str, str]:
    """
    Generate a short quiz covering the key points in the transcript.
    """
    _guard_payload(payload.transcript)

    try:
        quiz = generate_quiz(payload.transcript)
    except LanguageModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"quiz": quiz}


@app.post("/document-notes")
async def document_notes(file: UploadFile = File(...)) -> dict[str, str]:
    """
    Accept a PDF/DOCX/TXT upload and return structured notes from its text.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")

    try:
        text = _extract_text_from_upload(file.filename, contents)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _guard_payload(text)

    try:
        notes = generate_structured_notes(text)
    except LanguageModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"notes": notes}


@app.post("/youtube-notes")
def youtube_notes(payload: LinkPayload) -> dict[str, str]:
    """
    Fetch a YouTube transcript (if available) and generate structured notes from it.
    """
    video_id = _parse_youtube_id(payload.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    try:
        transcript_text = _fetch_youtube_transcript(video_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _guard_payload(transcript_text)

    try:
        notes = generate_structured_notes(transcript_text)
    except LanguageModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"notes": notes}


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """
    Provide a lightweight HTML playground for manual testing.
    """
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        html = (
            "<h1>StudyBUDY API</h1>"
            "<p>Static UI not found. Ensure static/index.html is available.</p>"
        )
    return HTMLResponse(content=html)


def _guard_payload(content: Optional[str]) -> None:
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Transcript content is required.")


def _extract_text_from_upload(filename: Optional[str], payload: bytes) -> str:
    if not filename:
        raise ValueError("Filename is required to determine document type.")
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt"}:
        return payload.decode("utf-8", errors="ignore")
    if suffix in {".pdf"}:
        reader = PdfReader(BytesIO(payload))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
        if not text.strip():
            raise RuntimeError("No text could be extracted from the PDF.")
        return text
    if suffix in {".docx", ".doc"}:
        document = Document(BytesIO(payload))
        text = "\n".join(p.text for p in document.paragraphs)
        if not text.strip():
            raise RuntimeError("No text could be extracted from the document.")
        return text
    raise ValueError("Unsupported file type. Use PDF, DOCX, DOC, or TXT.")


def _parse_youtube_id(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be"}:
        return parsed.path.lstrip("/")
    if parsed.hostname and "youtube" in parsed.hostname:
        query = parse_qs(parsed.query)
        if "v" in query and query["v"]:
            return query["v"][0]
        # handle /embed/<id> or /shorts/<id>
        parts = parsed.path.split("/")
        if len(parts) >= 2:
            return parts[-1]
    return None


def _fetch_youtube_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except (NoTranscriptFound, TranscriptsDisabled) as exc:
        raise RuntimeError("Transcript not available for this video.") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to fetch YouTube transcript: {exc}") from exc

    combined = " ".join(chunk.get("text", "") for chunk in transcript)
    if not combined.strip():
        raise RuntimeError("Received an empty transcript from YouTube.")
    return combined
