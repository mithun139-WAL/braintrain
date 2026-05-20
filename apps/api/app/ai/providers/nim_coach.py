"""
NIM coaching AI provider — uses LangChain ChatOpenAI pointed at NVIDIA NIM's
OpenAI-compatible endpoint to deliver personalized AI coaching.

This is used for PRO users when NVIDIA_API_KEY is configured.
NIM takes precedence over the OpenAI provider when both keys are present.
"""
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

_SYSTEM_TEMPLATE = """You are BrainTrain's elite AI communication coach — a combination of executive \
communication coach, behavioral interview expert, and career advisor.

Your primary goal is to help the user improve their {focus_area} skills for professional interviews \
and high-stakes communication.

{context_block}

Guidelines:
- Be warm, direct, and encouraging but never sycophantic
- Ask probing questions to uncover root causes of communication issues
- Give specific, actionable micro-exercises (< 5 minutes) when relevant
- Use frameworks: STAR, SBI, Rule of Three, Problem-Solution-Result
- Keep responses concise (3-5 sentences) unless the user asks for detail
- Celebrate specific wins, not generic praise
- If the user seems stuck, offer a concrete exercise instead of more advice"""


class NIMCoachProvider:
    """
    NVIDIA NIM-backed coaching provider using LangChain.
    Uses the OpenAI-compatible NIM endpoint via langchain-openai.
    Stateless — full conversation history is passed on each call.
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self._llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            max_tokens=512,
        )

    async def get_response(
        self,
        messages: List[dict],
        focus_area: str = "general",
        context_summary: str | None = None,
    ) -> str:
        """
        Generate an AI coaching response.

        messages: list of {"role": "user"|"assistant", "content": str}
        focus_area: coaching dimension
        context_summary: optional evaluation summary to include in system prompt
        """
        context_block = ""
        if context_summary:
            context_block = (
                f"Context from the user's most recent evaluation:\n{context_summary}\n\n"
                "Use this to give specific, personalized coaching based on their actual performance."
            )

        system_prompt = _SYSTEM_TEMPLATE.format(
            focus_area=focus_area,
            context_block=context_block,
        )

        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        response = await self._llm.ainvoke(lc_messages)
        return response.content
