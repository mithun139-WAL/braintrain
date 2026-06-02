import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.voice.state.interview_state import InterviewState
from app.ai.voice.conversation.memory import ConversationMessage
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_encoder import MemoryEncoder
from app.ai.voice.memory.vector_store import VectorStore
from app.ai.voice.memory.memory_store import MemoryStore
from app.ai.voice.memory.memory_decay import MemoryDecay
from app.ai.voice.memory.retrieval_ranker import RetrievalRanker
from app.ai.voice.memory.retrieval_policies import RetrievalPolicies
from app.ai.voice.memory.retrieval_engine import RetrievalEngine
from app.ai.voice.memory.session_summarizer import SessionSummarizer
from app.ai.voice.memory.memory_compactor import MemoryCompactor
from app.ai.voice.llm.response_generator import ResponseGenerator

logger = logging.getLogger("memory_pipeline")

class MemoryPipeline:
    def __init__(self):
        # Instantiate subcomponents
        self.encoder = MemoryEncoder()
        self.vector_store = VectorStore()
        self.memory_store = MemoryStore()
        self.decay_manager = MemoryDecay()
        self.ranker = RetrievalRanker()
        self.retrieval_engine = RetrievalEngine(
            encoder=self.encoder,
            vector_store=self.vector_store,
            memory_store=self.memory_store,
            decay_manager=self.decay_manager,
            ranker=self.ranker
        )
        # Mock/Inject response generator for session summarizer
        self.response_generator = ResponseGenerator()
        self.session_summarizer = SessionSummarizer(
            response_generator=self.response_generator,
            encoder=self.encoder
        )
        self.compactor = MemoryCompactor(
            memory_store=self.memory_store,
            vector_store=self.vector_store,
            encoder=self.encoder
        )

    async def retrieve_context_for_prompt(
        self,
        candidate_id: uuid.UUID,
        query_text: str,
        state: InterviewState,
        db: Optional[AsyncSession] = None
    ) -> str:
        """
        Retrieves relevant historical context and formats it as a compact prompt augmentation block.
        """
        try:
            # 1. Determine active context & filters
            context = RetrievalPolicies.get_policy_context(state)
            policy_filters = RetrievalPolicies.get_query_filters(context)

            # 2. Retrieve ranked memories
            memories = await self.retrieval_engine.retrieve_relevant_memories(
                candidate_id=candidate_id,
                query_text=query_text,
                policy_filters=policy_filters,
                context=context,
                db=db
            )

            if not memories:
                return ""

            # 3. Format as a concise, behaviorally useful text block
            prompt_parts = []
            prompt_parts.append("Candidate Historical Behavior Context (do not mention memory retrieval to candidate):")
            
            for m in memories:
                # Keep prompt injection light and concise
                prompt_parts.append(f"- {m.content}")

            return "\n".join(prompt_parts)
        except Exception as e:
            logger.error("memory_pipeline | failed to retrieve prompt context: %s", e)
            return ""

    async def process_session_end(
        self,
        candidate_id: uuid.UUID,
        session_id: uuid.UUID,
        messages: List[ConversationMessage],
        db: Optional[AsyncSession] = None
    ) -> int:
        """
        Synthesizes memory artifacts at session end:
        1. Analyzes transcription & extracts memories.
        2. Persists memories to DB.
        3. Compacts redundant/similar memories.
        """
        try:
            # 1. Extract memories via LLM
            extracted_memories = await self.session_summarizer.summarize_and_extract_memories(
                candidate_id=candidate_id,
                session_id=session_id,
                messages=messages
            )

            # 2. Save all memories to store
            for mem in extracted_memories:
                await self.memory_store.create_memory(mem, db=db)

            # 3. Compact similar memories to prevent clutter
            merged_count = await self.compactor.compact_candidate_memories(candidate_id)
            logger.info(
                "memory_pipeline | session_end_processed | candidate: %s | saved: %d | merged: %d",
                candidate_id, len(extracted_memories), merged_count
            )
            return len(extracted_memories) - merged_count
        except Exception as e:
            logger.error("memory_pipeline | session end processing failed: %s", e)
            return 0
