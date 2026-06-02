import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.adaptive.engine import determine_next_difficulty

logger = logging.getLogger("difficulty_policy")

class DifficultyPolicy:
    def __init__(self):
        """
        Policy encapsulating adaptive difficulty logic.
        """
        pass

    async def adjust_difficulty(self, db: AsyncSession, state) -> str:
        """
        Delegates to determine_next_difficulty to resolve the difficulty level
        and updates the InterviewState in place.
        """
        if state.adaptive_enabled:
            current_diff = state.difficulty
            next_diff = await determine_next_difficulty(db, uuid.UUID(state.session_id))
            
            if next_diff != current_diff:
                logger.info(
                    "difficulty_adjusted | session: %s | from: %s | to: %s",
                    state.session_id, current_diff, next_diff
                )
                state.difficulty = next_diff
            return next_diff
            
        return state.difficulty
