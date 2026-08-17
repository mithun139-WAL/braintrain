"""
Questions service — generates the next question for a session.

Algorithm (bank-first, with LLM fallback):
  1. Validate session exists, belongs to user, is ACTIVE
  2. Check question count < 20
  3. Determine difficulty (adaptive or session base)
  4. Try QuestionBank.pick_question() — bank hit = free, zero AI cost
  5. If bank miss → generate via LLM and auto-save to bank (dataset flywheel)
  6. Persist QuestionInstance with sequence_order = existing_count + 1
"""
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_question_gen_provider
from app.ai.protocols import QuestionGenerationInput
from app.adaptive.engine import determine_next_difficulty
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.question_bank import repository as bank_repo
from app.modules.questions import repository as repo
from app.modules.questions.schemas import QuestionResponse

logger = logging.getLogger(__name__)

_MAX_QUESTIONS_PER_SESSION = 20


async def generate_next_question(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> QuestionResponse:
    # 1. Validate session
    session = await repo.get_session_for_questions(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found")

    if session.status != "ACTIVE":
        raise BadRequestException("Questions can only be generated for ACTIVE sessions")

    # 2. Check question count
    existing_count = await repo.count_active_questions(db, session_id)
    if existing_count >= _MAX_QUESTIONS_PER_SESSION:
        raise BadRequestException("Maximum questions reached for this session")

    sequence_order = existing_count + 1

    # 3. Determine difficulty
    if session.adaptive:
        difficulty = await determine_next_difficulty(db, session_id)
    else:
        difficulty = session.difficulty

    # 3.5 Fetch RAG facts if TECHNICAL
    reference_facts = None
    if session.interview_type == "TECHNICAL":
        from app.ai.intelligence.retrieval.retrieval_pipeline import RetrievalPipeline, RetrievalQuery
        pipeline = RetrievalPipeline(db)
        query = RetrievalQuery(
            query_text=session.topic.name,
            interview_type="TECHNICAL",
            top_k=3,
        )
        chunks = await pipeline.retrieve_knowledge(query)
        if chunks:
            # Combine the chunks into a single facts string
            reference_facts = "\n\n".join([f"- {c.text}" for c in chunks])

    # 4. Bank-first selection
    bank_content = await bank_repo.pick_random_question(
        db,
        topic_id=session.topic_id,
        interview_type=session.interview_type or "TECHNICAL",
        difficulty=difficulty,
        user_id=user_id,
    )

    if bank_content:
        question_content = bank_content.content
        # Use bank's reference facts if it has them, else fallback to whatever we just fetched
        reference_facts = bank_content.reference_facts or reference_facts
        logger.debug("Session %s Q%d: served from bank", session_id, sequence_order)
    else:
        # 5. LLM generation path
        logger.info(
            "Session %s Q%d: bank miss → LLM generation", session_id, sequence_order
        )
        existing_questions = await repo.get_question_contents(db, session_id)
        gen_input = QuestionGenerationInput(
            topic_name=session.topic.name,
            topic_id=session.topic_id,
            difficulty=difficulty,
            interview_type=session.interview_type or "TECHNICAL",
            existing_questions=existing_questions,
            reference_facts=reference_facts,
        )

        provider = get_question_gen_provider()

        # Use generate_and_save if OpenAI (auto-saves to bank flywheel)
        if hasattr(provider, "generate_and_save"):
            generated = await provider.generate_and_save(gen_input, db)
        else:
            generated = await provider.generate(gen_input)

        question_content = generated.question_text
        reference_facts = generated.reference_facts

    # 6. Persist QuestionInstance
    question = await repo.create_question(
        db,
        session_id=session_id,
        content=question_content,
        difficulty=difficulty,
        sequence_order=sequence_order,
        reference_facts=reference_facts,
    )
    await db.commit()
    await db.refresh(question)

    return QuestionResponse.model_validate(question)
