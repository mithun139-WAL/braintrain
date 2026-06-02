"""
Context Orchestrator - Manages context assembly and hallucination prevention.

This orchestrator assembles context from multiple sources while:
1. Preventing hallucinations via VerifiedCandidateProfile
2. Managing token budgets
3. Prioritizing relevant information
4. Enforcing domain constraints
"""
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
import logging

from pydantic import BaseModel, Field

from app.ai.orchestrators.contracts.context_contracts import (
    ContextBudget,
    ContextSources,
    VerifiedCandidateProfile,
    HallucinationCheck,
    ContextAssembly,
    ContextPriority
)
from app.ai.orchestrators.contracts.interview_contracts import (
    InterviewPhase,
    InterviewDomain,
    InterviewConstraints
)
from app.ai.orchestrators.state.interview_runtime_state import InterviewRuntimeState

logger = logging.getLogger(__name__)


class ContextOrchestrator:
    """
    Orchestrator for context assembly and hallucination prevention.
    
    Key responsibilities:
    - Assemble context from multiple sources
    - Enforce token budgets
    - Prevent hallucinations via verification
    - Prioritize relevant information
    - Apply domain constraints
    """
    
    def __init__(
        self,
        default_budget: Optional[ContextBudget] = None
    ):
        self.default_budget = default_budget or ContextBudget()
        self.verified_profiles: Dict[str, VerifiedCandidateProfile] = {}
        
        logger.info("Initialized ContextOrchestrator")
    
    async def assemble_context(
        self,
        session_id: str,
        candidate_id: str,
        current_phase: InterviewPhase,
        domain: InterviewDomain,
        sources: ContextSources,
        constraints: InterviewConstraints,
        priority: ContextPriority = ContextPriority.BALANCED
    ) -> ContextAssembly:
        """
        Assemble context from multiple sources with budget enforcement.
        
        Priority order:
        1. Verified candidate profile (hallucination prevention)
        2. Current question/topic context
        3. Recent conversation history
        4. Domain-specific knowledge
        5. Resume/JD information
        6. Long-term memory
        """
        
        # Get or create verified profile
        verified_profile = await self._get_verified_profile(
            candidate_id,
            sources
        )
        
        # Calculate token allocations based on priority
        allocations = self._calculate_allocations(priority, current_phase)
        
        # Assemble components
        components = {}
        tokens_used = {}
        
        # 1. Verified profile (critical for hallucination prevention)
        profile_context, profile_tokens = await self._build_profile_context(
            verified_profile,
            allocations["verified_profile"]
        )
        components["verified_profile"] = profile_context
        tokens_used["verified_profile"] = profile_tokens
        
        # 2. Current conversation history
        history_context, history_tokens = await self._build_history_context(
            sources.conversation_history,
            allocations["conversation_history"],
            current_phase
        )
        components["conversation_history"] = history_context
        tokens_used["conversation_history"] = history_tokens
        
        # 3. Resume information (filtered by verified profile)
        resume_context, resume_tokens = await self._build_resume_context(
            sources.resume_text,
            verified_profile,
            allocations["resume"],
            current_phase
        )
        components["resume"] = resume_context
        tokens_used["resume"] = resume_tokens
        
        # 4. Job description
        jd_context, jd_tokens = await self._build_jd_context(
            sources.job_description,
            allocations["job_description"],
            domain
        )
        components["job_description"] = jd_context
        tokens_used["job_description"] = jd_tokens
        
        # 5. Knowledge base (domain-specific)
        knowledge_context, knowledge_tokens = await self._build_knowledge_context(
            sources.knowledge_retrieved,
            allocations["knowledge_base"],
            domain,
            constraints
        )
        components["knowledge_base"] = knowledge_context
        tokens_used["knowledge_base"] = knowledge_tokens
        
        # 6. Memory/notes
        memory_context, memory_tokens = await self._build_memory_context(
            sources.memory_entries,
            allocations["memory"],
            current_phase
        )
        components["memory"] = memory_context
        tokens_used["memory"] = memory_tokens
        
        # Calculate total tokens
        total_tokens = sum(tokens_used.values())
        
        # Enforce budget
        if total_tokens > self.default_budget.total_budget_tokens:
            logger.warning(
                f"Context budget exceeded: {total_tokens}/{self.default_budget.total_budget_tokens} "
                f"session={session_id}"
            )
            # Trim less important components
            components, tokens_used = await self._trim_context(
                components,
                tokens_used,
                self.default_budget.total_budget_tokens,
                priority
            )
            total_tokens = sum(tokens_used.values())
        
        # Assemble final context
        final_context = self._assemble_final_context(
            components,
            constraints
        )
        
        # Create assembly result
        assembly = ContextAssembly(
            context=final_context,
            total_tokens=total_tokens,
            tokens_by_source=tokens_used,
            verified_profile=verified_profile,
            constraints_applied=constraints,
            budget_used=ContextBudget(
                total_tokens=total_tokens,
                resume_tokens=tokens_used.get("resume", 0),
                job_description_tokens=tokens_used.get("job_description", 0),
                conversation_history_tokens=tokens_used.get("conversation_history", 0),
                knowledge_base_tokens=tokens_used.get("knowledge_base", 0),
                memory_tokens=tokens_used.get("memory", 0)
            )
        )
        
        logger.info(
            f"Context assembled: {total_tokens} tokens, "
            f"phase={current_phase.value}, session={session_id}"
        )
        
        return assembly
    
    async def _get_verified_profile(
        self,
        candidate_id: str,
        sources: ContextSources
    ) -> VerifiedCandidateProfile:
        """
        Get or create verified candidate profile.
        
        This is CRITICAL for hallucination prevention.
        The interviewer must NEVER reference projects, skills, or experiences
        that are not explicitly verified.
        """
        
        if candidate_id in self.verified_profiles:
            return self.verified_profiles[candidate_id]
        
        # Extract verified information from resume
        profile = await self._extract_verified_info(
            sources.resume_text,
            sources.conversation_history
        )
        
        self.verified_profiles[candidate_id] = profile
        return profile
    
    async def _extract_verified_info(
        self,
        resume_text: str,
        conversation_history: List[Dict[str, Any]]
    ) -> VerifiedCandidateProfile:
        """
        Extract verified information from resume and conversation.
        
        Only information explicitly mentioned should be included.
        """
        
        # Parse resume for explicit mentions
        verified_skills = self._extract_skills(resume_text)
        verified_projects = self._extract_projects(resume_text)
        verified_technologies = self._extract_technologies(resume_text)
        verified_companies = self._extract_companies(resume_text)
        
        # Extract from conversation (candidate explicitly mentioned)
        for turn in conversation_history:
            if turn.get("speaker") == "candidate":
                transcript = turn.get("transcript", "")
                # Extract additional verified info from candidate responses
                verified_skills.update(self._extract_skills(transcript))
                verified_technologies.update(self._extract_technologies(transcript))
        
        profile = VerifiedCandidateProfile(
            verified_skills=list(verified_skills),
            verified_projects=list(verified_projects),
            verified_technologies=list(verified_technologies),
            verified_companies=list(verified_companies),
            verified_experience_areas=[]
        )
        
        return profile
    
    def _extract_skills(self, text: str) -> Set[str]:
        """Extract skills from text."""
        # Simple keyword extraction (in production, use NLP)
        skills = set()
        skill_keywords = [
            "react", "vue", "angular", "node.js", "python", "java", "javascript",
            "typescript", "sql", "mongodb", "postgres", "redis", "docker", "kubernetes",
            "aws", "azure", "gcp", "git", "ci/cd", "rest", "graphql", "html", "css"
        ]
        
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                skills.add(skill)
        
        return skills
    
    def _extract_projects(self, text: str) -> Set[str]:
        """Extract project names from text."""
        # Simple project extraction (look for "Project:" or bullet points)
        projects = set()
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("Project:") or line.startswith("•") or line.startswith("-"):
                # Extract project name (first few words)
                words = line.replace("Project:", "").replace("•", "").replace("-", "").strip().split()
                if len(words) >= 2:
                    project_name = " ".join(words[:3])
                    projects.add(project_name)
        
        return projects
    
    def _extract_technologies(self, text: str) -> Set[str]:
        """Extract technologies from text."""
        return self._extract_skills(text)  # Similar to skills
    
    def _extract_companies(self, text: str) -> Set[str]:
        """Extract company names from text."""
        companies = set()
        # Look for common patterns like "at Company" or "Company - Position"
        import re
        
        # Pattern: word followed by " - " (common in resumes)
        pattern = r'([A-Z][a-zA-Z\s]+)\s*[-–—]'
        matches = re.findall(pattern, text)
        
        for match in matches:
            company = match.strip()
            if len(company.split()) <= 3:  # Reasonable company name length
                companies.add(company)
        
        return companies
    
    def _calculate_allocations(
        self,
        priority: ContextPriority,
        phase: InterviewPhase
    ) -> Dict[str, int]:
        """
        Calculate token allocations based on priority and phase.
        """
        
        total = self.default_budget.total_budget_tokens
        
        if priority == ContextPriority.CONVERSATION_HEAVY:
            return {
                "verified_profile": int(total * 0.10),
                "conversation_history": int(total * 0.40),
                "resume": int(total * 0.15),
                "job_description": int(total * 0.10),
                "knowledge_base": int(total * 0.15),
                "memory": int(total * 0.10)
            }
        
        elif priority == ContextPriority.KNOWLEDGE_HEAVY:
            return {
                "verified_profile": int(total * 0.10),
                "conversation_history": int(total * 0.20),
                "resume": int(total * 0.15),
                "job_description": int(total * 0.10),
                "knowledge_base": int(total * 0.35),
                "memory": int(total * 0.10)
            }
        
        elif priority == ContextPriority.CANDIDATE_FOCUSED:
            return {
                "verified_profile": int(total * 0.15),
                "conversation_history": int(total * 0.20),
                "resume": int(total * 0.30),
                "job_description": int(total * 0.15),
                "knowledge_base": int(total * 0.10),
                "memory": int(total * 0.10)
            }
        
        else:  # BALANCED
            return {
                "verified_profile": int(total * 0.10),
                "conversation_history": int(total * 0.25),
                "resume": int(total * 0.20),
                "job_description": int(total * 0.15),
                "knowledge_base": int(total * 0.20),
                "memory": int(total * 0.10)
            }
    
    async def _build_profile_context(
        self,
        profile: VerifiedCandidateProfile,
        budget: int
    ) -> tuple[str, int]:
        """Build verified profile context."""
        
        context_parts = []
        
        if profile.verified_skills:
            skills_str = ", ".join(profile.verified_skills[:10])
            context_parts.append(f"Verified Skills: {skills_str}")
        
        if profile.verified_technologies:
            tech_str = ", ".join(profile.verified_technologies[:10])
            context_parts.append(f"Verified Technologies: {tech_str}")
        
        if profile.verified_projects:
            projects_str = ", ".join(p.get("name", "") if isinstance(p, dict) else str(p) for p in profile.verified_projects[:5])
            context_parts.append(f"Verified Projects: {projects_str}")
        
        if profile.verified_companies:
            companies_str = ", ".join(profile.verified_companies[:3])
            context_parts.append(f"Verified Companies: {companies_str}")
        
        context = "\n".join(context_parts)
        tokens = self._estimate_tokens(context)
        
        # Trim if over budget
        if tokens > budget:
            context = context[:budget * 4]  # Rough char-to-token ratio
            tokens = budget
        
        return context, tokens
    
    async def _build_history_context(
        self,
        history: List[Dict[str, Any]],
        budget: int,
        phase: InterviewPhase
    ) -> tuple[str, int]:
        """Build conversation history context."""
        
        if not history:
            return "", 0
        
        # Take most recent turns
        recent_history = history[-10:]
        
        context_parts = []
        for turn in recent_history:
            speaker = turn.get("speaker", "unknown")
            transcript = turn.get("transcript", "")
            
            if speaker == "interviewer":
                context_parts.append(f"Q: {transcript}")
            else:
                context_parts.append(f"A: {transcript}")
        
        context = "\n".join(context_parts)
        tokens = self._estimate_tokens(context)
        
        # Trim if needed
        if tokens > budget:
            # Remove oldest turns
            while tokens > budget and context_parts:
                context_parts.pop(0)
                context = "\n".join(context_parts)
                tokens = self._estimate_tokens(context)
        
        return context, tokens
    
    async def _build_resume_context(
        self,
        resume_text: str,
        verified_profile: VerifiedCandidateProfile,
        budget: int,
        phase: InterviewPhase
    ) -> tuple[str, int]:
        """Build resume context filtered by verified profile."""
        
        if not resume_text:
            return "", 0
        
        # For early phases, include more resume detail
        if phase in [InterviewPhase.INTRODUCTION, InterviewPhase.RESUME_DISCUSSION]:
            context = resume_text
        else:
            # For later phases, extract only relevant sections
            context = self._extract_relevant_resume_sections(
                resume_text,
                phase
            )
        
        tokens = self._estimate_tokens(context)
        
        # Trim if needed
        if tokens > budget:
            context = context[:budget * 4]
            tokens = budget
        
        return context, tokens
    
    def _extract_relevant_resume_sections(
        self,
        resume_text: str,
        phase: InterviewPhase
    ) -> str:
        """Extract resume sections relevant to current phase."""
        
        # For technical phases, focus on skills and projects
        if phase in [
            InterviewPhase.TECHNICAL_ROUND_1,
            InterviewPhase.TECHNICAL_ROUND_2,
            InterviewPhase.SYSTEM_DESIGN
        ]:
            # Extract technical sections
            sections = ["Skills", "Technical Skills", "Projects", "Experience"]
        # For behavioral, focus on experience and achievements
        elif phase == InterviewPhase.BEHAVIORAL:
            sections = ["Experience", "Leadership", "Achievements"]
        else:
            return resume_text
        
        # Simple section extraction
        relevant_text = []
        lines = resume_text.split("\n")
        in_relevant_section = False
        
        for line in lines:
            line_upper = line.upper().strip()
            if any(section.upper() in line_upper for section in sections):
                in_relevant_section = True
            elif line_upper and line_upper.isupper() and len(line_upper.split()) <= 3:
                # Likely a new section header
                in_relevant_section = False
            
            if in_relevant_section:
                relevant_text.append(line)
        
        return "\n".join(relevant_text) if relevant_text else resume_text[:500]
    
    async def _build_jd_context(
        self,
        jd_text: str,
        budget: int,
        domain: InterviewDomain
    ) -> tuple[str, int]:
        """Build job description context."""
        
        if not jd_text:
            return "", 0
        
        context = jd_text
        tokens = self._estimate_tokens(context)
        
        if tokens > budget:
            context = context[:budget * 4]
            tokens = budget
        
        return context, tokens
    
    async def _build_knowledge_context(
        self,
        knowledge_chunks: List[str],
        budget: int,
        domain: InterviewDomain,
        constraints: InterviewConstraints
    ) -> tuple[str, int]:
        """Build knowledge base context with domain filtering."""
        
        if not knowledge_chunks:
            return "", 0
        
        # Filter by domain constraints
        filtered_chunks = []
        for chunk in knowledge_chunks:
            chunk_content = chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
            if self._is_chunk_relevant(chunk_content, constraints):
                filtered_chunks.append(chunk_content)
        
        context = "\n\n".join(filtered_chunks)
        tokens = self._estimate_tokens(context)
        
        # Trim if needed
        if tokens > budget:
            # Take top chunks until budget
            trimmed_chunks = []
            current_tokens = 0
            
            for chunk in filtered_chunks:
                chunk_tokens = self._estimate_tokens(chunk)
                if current_tokens + chunk_tokens <= budget:
                    trimmed_chunks.append(chunk)
                    current_tokens += chunk_tokens
                else:
                    break
            
            context = "\n\n".join(trimmed_chunks)
            tokens = current_tokens
        
        return context, tokens
    
    def _is_chunk_relevant(
        self,
        chunk: str,
        constraints: InterviewConstraints
    ) -> bool:
        """Check if knowledge chunk is relevant based on constraints."""
        
        chunk_lower = chunk.lower()
        
        # Check forbidden topics
        for forbidden in constraints.forbidden_topics:
            if forbidden.lower() in chunk_lower:
                return False
        
        # Check allowed topics (if specified)
        if constraints.allowed_topics:
            has_allowed = any(
                topic.lower() in chunk_lower
                for topic in constraints.allowed_topics
            )
            if not has_allowed:
                return False
        
        return True
    
    async def _build_memory_context(
        self,
        memory_entries: List[Dict[str, Any]],
        budget: int,
        phase: InterviewPhase
    ) -> tuple[str, int]:
        """Build memory/notes context."""
        
        if not memory_entries:
            return "", 0
        
        # Format memory entries
        context_parts = []
        for entry in memory_entries[-5:]:  # Most recent
            content = entry.get("content", "")
            context_parts.append(f"- {content}")
        
        context = "\n".join(context_parts)
        tokens = self._estimate_tokens(context)
        
        if tokens > budget:
            context = context[:budget * 4]
            tokens = budget
        
        return context, tokens
    
    def _assemble_final_context(
        self,
        components: Dict[str, str],
        constraints: InterviewConstraints
    ) -> str:
        """Assemble final context string."""
        
        parts = []
        
        # Add hallucination prevention notice
        parts.append("CRITICAL: Only reference information explicitly verified below. NEVER invent or assume candidate details.")
        parts.append("")
        
        if components.get("verified_profile"):
            parts.append("## Verified Candidate Information")
            parts.append(components["verified_profile"])
            parts.append("")
        
        if components.get("conversation_history"):
            parts.append("## Recent Conversation")
            parts.append(components["conversation_history"])
            parts.append("")
        
        if components.get("resume"):
            parts.append("## Resume Information")
            parts.append(components["resume"])
            parts.append("")
        
        if components.get("job_description"):
            parts.append("## Job Requirements")
            parts.append(components["job_description"])
            parts.append("")
        
        if components.get("knowledge_base"):
            parts.append("## Domain Knowledge")
            parts.append(components["knowledge_base"])
            parts.append("")
        
        if components.get("memory"):
            parts.append("## Interview Notes")
            parts.append(components["memory"])
            parts.append("")
        
        # Add constraints
        if constraints.forbidden_topics:
            parts.append(f"## Forbidden Topics: {', '.join(constraints.forbidden_topics)}")
        
        return "\n".join(parts)
    
    async def _trim_context(
        self,
        components: Dict[str, str],
        tokens_used: Dict[str, int],
        target_tokens: int,
        priority: ContextPriority
    ) -> tuple[Dict[str, str], Dict[str, int]]:
        """Trim context to fit budget."""
        
        # Define trim priority (higher = trim first)
        trim_priority = {
            "memory": 5,
            "knowledge_base": 4,
            "job_description": 3,
            "conversation_history": 2,
            "resume": 2,
            "verified_profile": 1  # NEVER trim this
        }
        
        current_total = sum(tokens_used.values())
        
        while current_total > target_tokens:
            # Find component to trim
            to_trim = None
            max_priority = 0
            
            for component, priority_val in trim_priority.items():
                if priority_val > max_priority and tokens_used.get(component, 0) > 50:
                    to_trim = component
                    max_priority = priority_val
            
            if not to_trim:
                break
            
            # Trim 20% from this component
            old_tokens = tokens_used[to_trim]
            new_tokens = int(old_tokens * 0.8)
            
            # Trim the actual text
            text = components[to_trim]
            new_text = text[:new_tokens * 4]  # Rough char-to-token
            
            components[to_trim] = new_text
            tokens_used[to_trim] = new_tokens
            
            current_total = sum(tokens_used.values())
        
        return components, tokens_used
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    async def check_for_hallucinations(
        self,
        generated_text: str,
        verified_profile: VerifiedCandidateProfile
    ) -> HallucinationCheck:
        """
        Check generated text for potential hallucinations.
        
        Returns violations if text references unverified information.
        """
        
        text_lower = generated_text.lower()
        violations = []
        
        # Check for unverified project references
        # Simple heuristic: look for "your project" or "you worked on"
        project_patterns = ["your project", "you worked on", "you built", "you developed"]
        
        for pattern in project_patterns:
            if pattern in text_lower:
                # Extract what follows the pattern
                idx = text_lower.index(pattern)
                snippet = generated_text[idx:idx+100]
                
                # Check if it matches verified projects
                matches_verified = any(
                    (p.get("name", "").lower() if isinstance(p, dict) else str(p).lower()) in snippet.lower()
                    for p in verified_profile.verified_projects
                )
                
                if not matches_verified:
                    violations.append(
                        f"Potential hallucination: References unverified project/work - '{snippet}'"
                    )
        
        # Check for unverified skill/technology claims
        skill_patterns = ["you have experience with", "you know", "you used"]
        
        for pattern in skill_patterns:
            if pattern in text_lower:
                idx = text_lower.index(pattern)
                snippet = generated_text[idx:idx+100]
                
                # Check against verified skills/technologies
                matches_verified = any(
                    (skill.lower() in snippet.lower() or tech.lower() in snippet.lower())
                    for skill in verified_profile.verified_skills
                    for tech in verified_profile.verified_technologies
                )
                
                if not matches_verified:
                    violations.append(
                        f"Potential hallucination: References unverified skill - '{snippet}'"
                    )
        
        is_safe = len(violations) == 0
        confidence = 1.0 if is_safe else max(0.0, 1.0 - len(violations) * 0.3)
        
        return HallucinationCheck(
            is_safe=is_safe,
            violations=violations,
            risk_level="low" if is_safe else "high"
        )
