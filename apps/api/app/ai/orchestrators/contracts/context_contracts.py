"""
Context orchestrator contracts.

Defines data models for context management and hallucination prevention.
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ContextSource(BaseModel):
    """Source of context information."""
    source_type: str  # resume, jd, memory, knowledge, conversation
    source_id: str
    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    token_count: int
    priority: int = Field(default=5, ge=1, le=10)  # 1 = highest


class ContextPriority(str, Enum):
    """Priority modes for context assembly."""
    BALANCED = "balanced"
    CONVERSATION_HEAVY = "conversation_heavy"
    KNOWLEDGE_HEAVY = "knowledge_heavy"
    CANDIDATE_FOCUSED = "candidate_focused"


class ContextSources(BaseModel):
    """Collection of raw context sources to assemble."""
    resume_text: str = ""
    job_description: str = ""
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_retrieved: List[Dict[str, Any]] = Field(default_factory=list)
    memory_entries: List[Dict[str, Any]] = Field(default_factory=list)


class VerifiedCandidateProfile(BaseModel):
    """Verified facts about the candidate."""
    
    # Verified skills
    verified_skills: List[str] = Field(default_factory=list)
    verified_technologies: List[str] = Field(default_factory=list)
    verified_tools: List[str] = Field(default_factory=list)
    
    # Verified experience
    verified_projects: List[Dict[str, Any]] = Field(default_factory=list)
    verified_companies: List[str] = Field(default_factory=list)
    verified_roles: List[str] = Field(default_factory=list)
    
    # Verified achievements
    verified_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    verified_outcomes: List[str] = Field(default_factory=list)
    
    # Conversation-verified facts
    conversation_verified_facts: Dict[str, Any] = Field(default_factory=dict)
    
    # Unverified mentions (candidate said but not confirmed)
    unverified_mentions: List[str] = Field(default_factory=list)


class RuntimeContext(BaseModel):
    """Context available for current turn."""
    
    # Resume context
    active_resume_context: str = ""
    resume_chunks_used: List[str] = Field(default_factory=list)
    
    # Job description context
    active_jd_context: str = ""
    jd_chunks_used: List[str] = Field(default_factory=list)
    
    # Memory context
    relevant_memory: str = ""
    memory_chunks_used: List[ContextSource] = Field(default_factory=list)
    
    # Retrieved knowledge
    retrieved_knowledge: str = ""
    knowledge_chunks_used: List[ContextSource] = Field(default_factory=list)
    
    # Interview constraints
    interview_constraints: str = ""
    active_topics: List[str] = Field(default_factory=list)
    forbidden_topics: List[str] = Field(default_factory=list)
    
    # Conversation history (compressed)
    recent_conversation: str = ""
    conversation_turns_included: int = 0
    
    # Verified profile
    verified_profile: VerifiedCandidateProfile
    
    # Total token budget
    total_tokens: int = 0
    max_tokens: int = 4000


class ContextBudget(BaseModel):
    """Token budget allocation for context."""
    
    # Budget planning fields
    system_prompt_tokens: int = 500
    interview_rules_tokens: int = 200
    resume_context_tokens: int = 800
    jd_context_tokens: int = 400
    memory_context_tokens: int = 600
    knowledge_context_tokens: int = 800
    conversation_history_tokens: int = 800
    persona_tokens: int = 300
    response_buffer_tokens: int = 600
    
    total_budget_tokens: int = 5000
    
    # Actual usage tracking fields (for reporting)
    total_tokens: int = 0
    resume_tokens: int = 0
    job_description_tokens: int = 0
    knowledge_base_tokens: int = 0
    memory_tokens: int = 0
    
    def validate_budget(self) -> bool:
        """Check if allocation fits within budget."""
        allocated = (
            self.system_prompt_tokens +
            self.interview_rules_tokens +
            self.resume_context_tokens +
            self.jd_context_tokens +
            self.memory_context_tokens +
            self.knowledge_context_tokens +
            self.conversation_history_tokens +
            self.persona_tokens +
            self.response_buffer_tokens
        )
        return allocated <= self.total_budget_tokens


class HallucinationCheck(BaseModel):
    """Result of hallucination prevention check."""
    
    is_safe: bool
    violations: List[str] = Field(default_factory=list)
    risk_level: str  # low, medium, high, critical
    
    # Specific checks
    references_unverified_experience: bool = False
    invents_project_details: bool = False
    assumes_unverified_tech: bool = False
    attributes_false_ownership: bool = False
    
    # Corrections
    suggested_correction: Optional[str] = None
    safe_alternative: Optional[str] = None


class ContextCompressionStrategy(BaseModel):
    """Strategy for compressing context."""
    
    strategy_name: str  # summarize, truncate, semantic_filter, hierarchical
    max_tokens: int
    preserve_recent_turns: int = 3
    preserve_key_facts: bool = True
    remove_filler: bool = True


class ContextRetrievalQuery(BaseModel):
    """Query for retrieving relevant context."""
    
    query_text: str
    context_types: List[str] = Field(default_factory=list)  # resume, jd, memory, knowledge
    
    # Filters
    domain_filter: Optional[str] = None
    topic_filter: Optional[str] = None
    recency_weight: float = 0.5
    
    # Limits
    max_chunks: int = 5
    max_tokens: int = 1000
    similarity_threshold: float = 0.7


class ContextAssemblyRequest(BaseModel):
    """Request to assemble context for turn."""
    
    session_id: str
    current_question: Optional[str] = None
    candidate_last_response: Optional[str] = None
    
    # Context requirements
    include_resume: bool = True
    include_jd: bool = True
    include_memory: bool = True
    include_knowledge: bool = False
    
    # Budget
    budget: ContextBudget
    
    # Compression
    enable_compression: bool = True
    compression_strategy: Optional[ContextCompressionStrategy] = None


class ContextValidationResult(BaseModel):
    """Result of context validation."""
    
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Checks
    within_token_budget: bool = True
    no_hallucination_risk: bool = True
    no_topic_drift: bool = True
    contains_required_context: bool = True
    
    # Metrics
    total_tokens: int
    context_quality_score: float = Field(ge=0.0, le=1.0)


class AttributionCheck(BaseModel):
    """Check if attribution is correctly grounded."""
    
    statement: str
    attribution_target: str  # "candidate", "resume", "conversation"
    
    is_grounded: bool
    evidence_source: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    
    # If not grounded
    hallucination_type: Optional[str] = None  # invented_project, false_tech, etc.
    safe_reformulation: Optional[str] = None


class ContextAssembly(BaseModel):
    """Result of context assembly operation."""
    
    # Assembled context
    context: str
    total_tokens: int
    tokens_by_source: Dict[str, int] = Field(default_factory=dict)
    
    # Components
    verified_profile: VerifiedCandidateProfile
    constraints_applied: Any  # InterviewConstraints (avoiding circular import)
    budget_used: ContextBudget
    
    # Metadata
    assembly_timestamp: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
