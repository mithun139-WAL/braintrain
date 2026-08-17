from pydantic import BaseModel


class DiagramElement(BaseModel):
    type: str
    x: float = 0.0
    y: float = 0.0
    width: float | None = None
    height: float | None = None
    text: str | None = None
    strokeColor: str | None = None
    backgroundColor: str | None = None
    roughness: int | None = None
    strokeWidth: int | None = None
    points: list[list[float]] | None = None
    fontSize: int | None = None


class DiagramScene(BaseModel):
    elements: list[DiagramElement]


class ChatMessage(BaseModel):
    role: str
    content: str


class GenerateRequest(BaseModel):
    prompt: str
    existing_elements: list[DiagramElement] | None = None
    history: list[ChatMessage] | None = None


class GenerateResponse(BaseModel):
    scene: DiagramScene
    explanation: str | None = None
    prompt: str | None = None


class TranscribeResponse(BaseModel):
    text: str

