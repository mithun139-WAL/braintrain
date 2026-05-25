import os
import logging
from typing import Any

logger = logging.getLogger("prompt_manager")

class PromptManager:
    def __init__(self, templates_dir: str = None, response_cache: Any = None):
        """
        Manages loading and rendering of prompt templates from disk.
        """
        if not templates_dir:
            templates_dir = os.path.join(os.path.dirname(__file__), "prompt_templates")
        self.templates_dir = templates_dir
        self.response_cache = response_cache
        logger.info("Initialized PromptManager with templates directory: %s", self.templates_dir)

    def _load_template(self, relative_path: str) -> str:
        full_path = os.path.join(self.templates_dir, relative_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.debug("Successfully loaded template: %s", relative_path)
                return content
        except Exception as exc:
            logger.warning("Failed to load prompt template at %s: %s", relative_path, exc)
            return ""

    def get_system_prompt(self, is_panel: bool = False) -> str:
        """Loads stable system configuration instructions."""
        filename = "base/system_panel.txt" if is_panel else "base/system.txt"
        return self._load_template(filename)

    def get_interview_prompt(self) -> str:
        """Loads the default interviewer identity template."""
        return self._load_template("base/interviewer.txt")

    def get_followup_prompt(self, topic: str = None) -> str:
        """
        Loads technical followup context instructions.
        Maps raw topics to specific template files if they match a known category.
        """
        if not topic:
            return ""
        
        # Normalize topic string to match file names
        topic_lower = topic.lower().strip()
        if "backend" in topic_lower:
            return self._load_template("technical/backend.txt")
        elif "frontend" in topic_lower:
            return self._load_template("technical/frontend.txt")
        elif "ai" in topic_lower or "machine learning" in topic_lower:
            return self._load_template("technical/ai_engineering.txt")
        elif "system design" in topic_lower or "architecture" in topic_lower:
            return self._load_template("technical/system_design.txt")
        
        return ""

    def get_clarification_prompt(self) -> str:
        """Loads clarification/recovery template instructions."""
        return self._load_template("behavioral/clarification.txt")

    def get_behavioral_prompt(self, objective: str) -> str:
        """Loads dynamic behavioral objectives such as encouragement or challenge."""
        objective_lower = objective.lower().strip()
        if "encouragement" in objective_lower or "encourage" in objective_lower:
            return self._load_template("behavioral/encouragement.txt")
        elif "challenge" in objective_lower:
            return self._load_template("behavioral/challenge.txt")
        elif "clarification" in objective_lower or "clarify" in objective_lower:
            return self._load_template("behavioral/clarification.txt")
        return ""

    def get_panel_prompt(self, panelist: str) -> str:
        """Loads profile personality description for a specific panelist."""
        panelist_lower = panelist.lower().strip()
        filename = f"panel/{panelist_lower}.txt"
        return self._load_template(filename)
