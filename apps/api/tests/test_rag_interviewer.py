import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.retriever import InterviewKnowledgeRetriever
from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.decisions.decision import ConversationDecision
from app.ai.voice.decisions.action import InterviewAction
from app.ai.voice.llm.interviewer import Interviewer
from app.ai.voice.llm.builders.interview_prompt_builder import InterviewPromptBuilder
from app.ai.voice.llm.prompt_manager import PromptManager
from app.ai.voice.policies.response_policy import ResponsePolicy
from app.ai.voice.policies.fact_grounding_policy import FactGroundingPolicy
from app.ai.voice.llm.response_generator import ResponseGenerator
from app.ai.voice.llm.response_parser import ResponseParser
from app.ai.voice.llm.formatters.speaker_formatter import SpeakerFormatter
from app.ai.voice.llm.formatters.response_formatter import ResponseFormatter
from app.ai.voice.llm.builders.system_prompt_builder import SystemPromptBuilder
from app.ai.voice.llm.builders.followup_prompt_builder import FollowupPromptBuilder
from app.ai.voice.llm.builders.clarification_prompt_builder import ClarificationPromptBuilder

@pytest.mark.asyncio
async def test_knowledge_retriever_empty():
    retriever = InterviewKnowledgeRetriever()
    db = AsyncMock(spec=AsyncSession)
    
    # Test short query is skipped
    res = await retriever.retrieve_context(db, query_text="ab")
    assert res == ""

@pytest.mark.asyncio
async def test_knowledge_retriever_success():
    retriever = InterviewKnowledgeRetriever()
    db = AsyncMock(spec=AsyncSession)
    
    # Mock pipeline retrieval returning chunks
    mock_chunk = MagicMock()
    mock_chunk.text = "This is a caching strategy guide"
    mock_chunk.document_title = "Caching Guide"
    mock_chunk.domain = "backend"
    mock_chunk.topic = "caching"
    mock_chunk.metadata = {}
    
    retriever.pipeline.retrieve = AsyncMock(return_value=[mock_chunk])
    
    res = await retriever.retrieve_context(db, query_text="Explain caching tradeoffs", domain="backend")
    assert "Caching Guide" in res
    assert "This is a caching strategy guide" in res

@pytest.mark.asyncio
async def test_interviewer_respond_injects_rag():
    # Setup interviewer mock components
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_behavioral_prompt.return_value = "Keep it concise"
    
    system_prompt_builder = MagicMock(spec=SystemPromptBuilder)
    system_prompt_builder.build.return_value = "System prompt"
    
    interview_prompt_builder = InterviewPromptBuilder(prompt_manager)
    followup_prompt_builder = MagicMock(spec=FollowupPromptBuilder)
    followup_prompt_builder.build_followup.return_value = ""
    
    clarification_prompt_builder = MagicMock(spec=ClarificationPromptBuilder)
    clarification_prompt_builder.build_clarification.return_value = ""
    
    response_generator = AsyncMock(spec=ResponseGenerator)
    response_generator.generate.return_value = "interviewer: Let's discuss database optimization."
    
    response_parser = ResponseParser()
    speaker_formatter = SpeakerFormatter()
    response_formatter = ResponseFormatter()
    response_policy = MagicMock(spec=ResponsePolicy)
    response_policy.select_tone.return_value = "professional"
    
    interviewer = Interviewer(
        prompt_manager=prompt_manager,
        system_prompt_builder=system_prompt_builder,
        interview_prompt_builder=interview_prompt_builder,
        followup_prompt_builder=followup_prompt_builder,
        clarification_prompt_builder=clarification_prompt_builder,
        response_generator=response_generator,
        response_parser=response_parser,
        speaker_formatter=speaker_formatter,
        response_formatter=response_formatter,
        response_policy=response_policy
    )
    
    # Mock retriever
    mock_retriever = AsyncMock()
    mock_retriever.retrieve_context.return_value = "Dummy RAG Context"
    interviewer.knowledge_retriever = mock_retriever
    
    # State setup
    state = MagicMock()
    state.difficulty = "MEDIUM"
    state.adaptive_enabled = True
    state.conversation.turn_count = 1
    state.conversation.current_topic = "backend"
    
    # Setup candidate message history
    msg1 = MagicMock()
    msg1.role = "Candidate"
    msg1.content = "I used Redis for caching."
    state.conversation.messages = [msg1]
    
    state.candidate.confidence_score = 80.0
    state.pressure_level = "NORMAL"
    state.panel_mode = False
    state.behavioral_signals = None
    
    decision = MagicMock()
    decision.action = InterviewAction.ASK_FOLLOWUP
    decision.reason = "Candidate mentioned caching"
    
    # Call respond and capture generated prompts
    with patch.object(interviewer.interview_prompt_builder, 'build', wraps=interviewer.interview_prompt_builder.build) as spy_build:
        res = await interviewer.respond(state, decision)
        
        # Verify retriever was called with candidate last reply
        mock_retriever.retrieve_context.assert_called_once()
        # Verify prompt builder build got the rag_context
        spy_build.assert_called_once()
        assert spy_build.call_args[1]["rag_context"] == "Dummy RAG Context"
        
        # Verify the prompt generated includes the grounding tag
        messages_sent = response_generator.generate.call_args[0][0]
        system_msg_with_directives = messages_sent[-1]["content"]
        assert "Dummy RAG Context" in system_msg_with_directives
        assert "[KNOWLEDGE BASE GROUNDING CONTEXT:" in system_msg_with_directives
