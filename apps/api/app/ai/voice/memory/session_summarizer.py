import json
import uuid
import logging
from typing import List, Dict, Any
from app.ai.voice.conversation.memory import ConversationMessage
from app.ai.voice.memory.memory_types import MemoryObject, MemoryType
from app.ai.voice.memory.memory_encoder import MemoryEncoder
from app.ai.voice.llm.response_generator import ResponseGenerator

logger = logging.getLogger("session_summarizer")

class SessionSummarizer:
    def __init__(self, response_generator: ResponseGenerator, encoder: MemoryEncoder):
        self.response_generator = response_generator
        self.encoder = encoder

    async def summarize_and_extract_memories(
        self,
        candidate_id: uuid.UUID,
        session_id: uuid.UUID,
        messages: List[ConversationMessage]
    ) -> List[MemoryObject]:
        """
        Parses session messages and extracts key memories using the LLM.
        Converts the results into fully initialized MemoryObjects.
        """
        if not messages:
            return []

        # Format transcript
        transcript_lines = []
        for msg in messages:
            speaker = msg.speaker or ("Candidate" if msg.role == "user" else "Interviewer")
            transcript_lines.append(f"{speaker}: {msg.content}")
        
        transcript = "\n".join(transcript_lines)

        system_prompt = (
            "You are a staff-level AI behavior analyst. Analyze the following interview transcript and extract exactly 2-5 critical candidate observations. "
            "Group them into: SEMANTIC (skills, technologies, preferences), EPISODIC (memorable moments, notable breakthroughs/failures), "
            "or BEHAVIORAL (hesitation patterns, verbosity, confidence shifts, stress reactions).\n\n"
            "Respond ONLY with a valid JSON array of objects with the following schema, and no other text or markdown codeblocks:\n"
            "[\n"
            "  {\n"
            "    \"type\": \"SEMANTIC\" | \"EPISODIC\" | \"BEHAVIORAL\",\n"
            "    \"content\": \"Brief, dense, behaviorally useful summary statement (max 15 words). No raw transcripts.\",\n"
            "    \"importance\": 0.1 to 1.0 (float reflecting long-term signal importance),\n"
            "    \"tags\": [\"lowercase-tag1\", \"lowercase-tag2\"]\n"
            "  }\n"
            "]"
        )

        user_prompt = f"Transcript:\n{transcript}"

        llm_payload = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info("session_summarizer | calling LLM to extract memories for session %s", session_id)
        raw_response = await self.response_generator.generate(llm_payload)
        
        if not raw_response:
            logger.error("session_summarizer | LLM returned empty response")
            return []

        # Parse JSON
        extracted_data = []
        try:
            # Strip out markdown blocks if present
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            extracted_data = json.loads(clean_json)
        except Exception as e:
            logger.exception("session_summarizer | failed to parse LLM JSON response: %s", raw_response)
            return []

        if not isinstance(extracted_data, list):
            logger.error("session_summarizer | parsed JSON is not a list")
            return []

        memories = []
        for item in extracted_data:
            try:
                mtype_str = item.get("type", "EPISODIC").upper()
                mtype = MemoryType.EPISODIC
                if mtype_str == "SEMANTIC":
                    mtype = MemoryType.SEMANTIC
                elif mtype_str == "BEHAVIORAL":
                    mtype = MemoryType.BEHAVIORAL

                content = item.get("content", "").strip()
                if not content:
                    continue

                importance = float(item.get("importance", 0.5))
                tags = [str(t).lower() for t in item.get("tags", [])]

                # Generate vector embedding asynchronously
                embedding = await self.encoder.encode(content)

                memory_obj = MemoryObject(
                    memory_id=uuid.uuid4(),
                    candidate_id=candidate_id,
                    memory_type=mtype,
                    content=content,
                    embedding=embedding,
                    confidence_score=1.0,
                    importance_score=importance,
                    source_session_id=session_id,
                    behavioral_tags=tags,
                    decay_factor=1.0
                )
                memories.append(memory_obj)
            except Exception as e:
                logger.error("session_summarizer | error parsing individual memory item: %s", e)

        logger.info("session_summarizer | extracted %d memories from session %s", len(memories), session_id)
        return memories
