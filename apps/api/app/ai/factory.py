"""
AI provider factory — returns the correct provider implementations based on config.

LLM task priority (evaluation, question gen, coaching):
  1. NVIDIA NIM (NVIDIA_API_KEY starts with "nvapi-")  → NIM providers
  2. OpenAI    (OPENAI_API_KEY starts with "sk-")       → OpenAI providers
  3. Fallback                                           → Stub providers (zero-cost local dev)

Audio transcription priority:
  1. Groq      (GROQ_API_KEY starts with "gsk_")        → whisper-large-v3 on Groq LPUs
  2. OpenAI    (OPENAI_API_KEY starts with "sk-")        → Whisper-1
  3. Fallback                                            → Stub provider
  Note: NVIDIA NIM has no Whisper endpoint, so it is never used for transcription.

Usage:
    from app.ai.factory import get_question_gen_provider, get_evaluation_provider, get_transcription_provider
    provider = get_evaluation_provider()
    signal = await provider.evaluate(input)
"""
from functools import lru_cache

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_question_gen_provider():
    """Return the question generation provider (NIM > OpenAI > Stub)."""
    settings = get_settings()

    if settings.nim_enabled:
        from app.ai.providers.nim_question_gen import NIMQuestionGenerationProvider
        return NIMQuestionGenerationProvider(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            model=settings.nvidia_model,
        )

    if settings.openai_enabled:
        from app.ai.providers.openai_question_gen import OpenAIQuestionGenerationProvider
        return OpenAIQuestionGenerationProvider(api_key=settings.openai_api_key)

    from app.ai.providers.stub_question_gen import StubQuestionGenerationProvider
    return StubQuestionGenerationProvider()


@lru_cache(maxsize=1)
def get_evaluation_provider():
    """Return the answer evaluation provider (NIM > OpenAI > Stub)."""
    settings = get_settings()

    if settings.nim_enabled:
        from app.ai.providers.nim_evaluation import NIMEvaluationProvider
        return NIMEvaluationProvider(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            model=settings.nvidia_model,
        )

    if settings.openai_enabled:
        from app.ai.providers.openai_evaluation import OpenAIEvaluationProvider
        return OpenAIEvaluationProvider(api_key=settings.openai_api_key)

    from app.ai.providers.stub_evaluation import StubEvaluationProvider
    return StubEvaluationProvider()


@lru_cache(maxsize=1)
def get_transcription_provider():
    """
    Return the audio transcription provider.

    Priority: Groq (whisper-large-v3) → OpenAI (Whisper-1) → Stub.
    NIM is never used for transcription — it has no audio endpoint.
    """
    settings = get_settings()

    if settings.groq_enabled:
        from app.ai.providers.groq_transcription import GroqTranscriptionProvider
        return GroqTranscriptionProvider(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            model=settings.groq_whisper_model,
        )

    if settings.openai_enabled:
        from app.ai.providers.openai_transcription import OpenAITranscriptionProvider
        return OpenAITranscriptionProvider(api_key=settings.openai_api_key)

    from app.ai.providers.stub_transcription import StubTranscriptionProvider
    return StubTranscriptionProvider()


@lru_cache(maxsize=1)
def get_coach_provider():
    """Return the AI coaching provider (NIM > OpenAI > Stub)."""
    settings = get_settings()

    if settings.nim_enabled:
        from app.ai.providers.nim_coach import NIMCoachProvider
        return NIMCoachProvider(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            model=settings.nvidia_model,
        )

    if settings.openai_enabled:
        from app.ai.providers.langchain_coach import LangChainCoachProvider
        return LangChainCoachProvider(api_key=settings.openai_api_key)

    from app.ai.providers.stub_coach import StubCoachProvider
    return StubCoachProvider()
