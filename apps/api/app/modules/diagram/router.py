import tempfile
import os
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from openai import OpenAI

from app.core.config import get_settings, Settings
from app.modules.diagram.schemas import (
    GenerateRequest,
    GenerateResponse,
    DiagramScene,
    DiagramElement,
    TranscribeResponse,
)
from app.modules.diagram.service import DiagramService

router = APIRouter(prefix="/diagram", tags=["diagram"])


def _get_diagram_service(settings: Settings = Depends(get_settings)) -> DiagramService:
    try:
        return DiagramService(settings)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


def _get_transcription_client(settings: Settings) -> tuple[OpenAI, str]:
    """Groq (free, open-source Whisper) → OpenAI (paid)."""
    if settings.groq_enabled:
        return OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url), settings.groq_whisper_model
    if settings.openai_enabled:
        return OpenAI(api_key=settings.openai_api_key), "whisper-1"
    raise RuntimeError(
        "No transcription provider configured. "
        "Set GROQ_API_KEY (free, gsk_...) or OPENAI_API_KEY (paid, sk-...)."
    )


@router.post("/generate", response_model=GenerateResponse, response_model_exclude_none=True)
async def generate_diagram(
    req: GenerateRequest,
    service: DiagramService = Depends(_get_diagram_service),
):
    existing = [e.model_dump() for e in req.existing_elements] if req.existing_elements else None
    history = [h.model_dump() for h in req.history] if req.history else None
    elements, explanation = service.generate(req.prompt, existing, history)
    return GenerateResponse(
        scene=DiagramScene(elements=[DiagramElement(**e) for e in elements]),
        explanation=explanation,
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    try:
        client, model = _get_transcription_client(settings)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    suffix = ".wav" if file.filename and file.filename.endswith(".wav") else ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(model=model, file=audio)
        return TranscribeResponse(text=transcript.text)
    finally:
        os.unlink(tmp_path)


@router.post("/voice-diagram", response_model=GenerateResponse, response_model_exclude_none=True)
async def voice_diagram(
    file: UploadFile = File(...),
    existing_elements: str | None = Form(None),
    history: str | None = Form(None),
    service: DiagramService = Depends(_get_diagram_service),
    settings: Settings = Depends(get_settings),
):
    try:
        client, model = _get_transcription_client(settings)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    suffix = ".wav" if file.filename and file.filename.endswith(".wav") else ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(model=model, file=audio)
        prompt = transcript.text
    finally:
        os.unlink(tmp_path)

    parsed_existing = json.loads(existing_elements) if existing_elements else None
    parsed_history = json.loads(history) if history else None

    elements, explanation = service.generate(prompt, parsed_existing, parsed_history)
    return GenerateResponse(
        scene=DiagramScene(elements=[DiagramElement(**e) for e in elements]),
        explanation=explanation,
        prompt=prompt,
    )

