import json
import logging
from openai import OpenAI

from app.core.config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a system design diagram generator. Given a system design prompt, output a JSON object with:
- `elements`: array of Excalidraw-compatible diagram elements
- `explanation`: a short 1-sentence explanation of what was built

Rules for elements:
- Every service/component should be a `rectangle` with unique bounding box
- Every label should be a `text` element positioned near/inside its component
- Connections should use `arrow` elements with `points` being [[x1,y1],[x2,y2]]
- Use `roughness: 1` for the hand-drawn Excalidraw look
- Use muted colors (blues, grays, greens) for backgrounds
- Position elements left-to-right: client on left, CDN/API gateway, services, DBs on right
- Keep at least 150px spacing between boxes to prevent text labels from overlapping
- Arrows should connect the right edge of one box to the left edge of another

Rules for refinement/conversation:
- When refining or modifying an existing diagram, preserve the elements that are still relevant. Do not discard unchanged components. Keep their general positions or adjust them minimally to make room for new components.
- Maintain consistency in names, colors, and layout between turns.

Return ONLY valid JSON, no markdown fences, no commentary."""


class DiagramService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client, self.model = self._build_client()

    def _build_client(self) -> tuple[OpenAI, str]:
        s = self.settings
        if s.github_models_enabled:
            return OpenAI(api_key=s.github_token, base_url=s.github_models_base_url), s.github_model
        if s.nim_enabled:
            return OpenAI(api_key=s.nvidia_api_key, base_url=s.nvidia_base_url), s.nvidia_model
        if s.openai_enabled:
            return OpenAI(api_key=s.openai_api_key), "gpt-4o"
        raise RuntimeError("No AI provider configured. Set NVIDIA_API_KEY, GITHUB_TOKEN, or OPENAI_API_KEY.")

    def generate(
        self,
        prompt: str,
        existing_elements: list | None = None,
        history: list[dict] | None = None,
    ) -> tuple[list[dict], str]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        user_msg = f"User request: {prompt}"
        if existing_elements:
            user_msg += f"\nRefine the existing diagram: {json.dumps(existing_elements)}"
        else:
            user_msg += "\nDesign a new system architecture diagram from scratch."

        messages.append({"role": "user", "content": user_msg})

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4000,
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)
        elements = data.get("elements", [])
        explanation = data.get("explanation", "Diagram generated.")
        return elements, explanation

