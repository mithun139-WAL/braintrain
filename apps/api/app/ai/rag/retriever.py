import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.intelligence.retrieval.retrieval_pipeline import (
    HybridRetrievalPipeline,
    RetrievalQuery,
)
from app.ai.voice.memory.memory_encoder import MemoryEncoder

logger = logging.getLogger("interview_knowledge_retriever")

class InterviewKnowledgeRetriever:
    """
    Retrieves and formats curated interview Q&A chunks to ground the interviewer.
    """
    def __init__(self):
        self.encoder = MemoryEncoder()
        # Use HybridRetrievalPipeline for combined semantic + keyword search
        self.pipeline = HybridRetrievalPipeline(
            embedding_generator=self.encoder.encode
        )

    async def retrieve_context(
        self,
        db: AsyncSession,
        query_text: str,
        domain: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        top_k: int = 3,
    ) -> str:
        """
        Retrieves matching chunks and builds a formatted context string.
        """
        if not query_text or len(query_text.strip()) < 3:
            return ""

        try:
            # Build query specification
            query = RetrievalQuery(
                query_text=query_text,
                domain=domain,
                topic=topic,
                difficulty=difficulty,
                top_k=top_k,
                similarity_threshold=0.6,  # Permissive similarity threshold
            )

            # Perform retrieval
            chunks = await self.pipeline.retrieve(db=db, query=query)

            if not chunks:
                logger.debug("No knowledge chunks found for query: '%s'", query_text[:50])
                return ""

            # Format the retrieved chunks for LLM context injection
            context = self.pipeline.build_context(chunks, max_tokens=1000)
            logger.info("Retrieved %d grounding chunks from knowledge base", len(chunks))
            return context

        except Exception as exc:
            logger.error("Failed to retrieve knowledge context: %s", exc, exc_info=True)
            return ""
