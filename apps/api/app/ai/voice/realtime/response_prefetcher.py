import logging
from typing import Dict, Optional
from app.ai.voice.llm.prompt_manager import PromptManager

logger = logging.getLogger("response_prefetcher")

class ResponsePrefetcher:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        # Pre-built standard followup prompts mapped to keywords
        self.prefetch_templates: Dict[str, str] = {
            "caching": (
                "Probe candidate on caching details: ask about eviction strategies (LRU, LFU), "
                "invalidation, write-through vs write-back policies, or cache stampede mitigation."
            ),
            "scaling": (
                "Probe candidate on scale details: ask about microservices decomposition, "
                "horizontal replication, database sharding, consistency models, or load balancing."
            ),
            "optimization": (
                "Probe candidate on query/memory optimization: ask about query indexing, B-Trees, "
                "profiling tools, garbage collection bottlenecks, or runtime performance profiles."
            ),
        }

    def prefetch_context(self, active_topic: str) -> Optional[str]:
        """
        Prefetches the next hypothetical followup topic context guidelines in advance 
        based on active topic keywords.
        """
        if not active_topic:
            return None

        topic_lower = active_topic.lower()
        for kw, prompt_str in self.prefetch_templates.items():
            if kw in topic_lower:
                logger.info("response_prefetcher | prefetch hit for keyword: %s", kw)
                return prompt_str

        # Fallback to general followup template from PromptManager
        general_followup = self.prompt_manager.get_followup_prompt(active_topic)
        if general_followup:
            logger.info("response_prefetcher | loaded generic followup template from manager")
            return general_followup
            
        return None
