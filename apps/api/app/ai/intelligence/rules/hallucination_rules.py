"""
Hallucination Rules Engine.

Prevents the interviewer from:
- Inventing candidate experiences
- Assuming unverified knowledge
- Referencing non-existent projects
- Making unsupported claims about candidate background
"""
from typing import Dict, List, Any, Optional
import logging
import re

from app.ai.intelligence.rules.rule_engine import (
    RuleEngine, Rule, RuleType, RuleSeverity, RuleViolation
)

logger = logging.getLogger(__name__)


class HallucinationRuleEngine(RuleEngine):
    """
    Specialized rule engine for preventing hallucinations.
    
    Validates that interviewer responses only reference:
    - Verified candidate profile data
    - Current conversation history
    - Retrieved knowledge (with proper grounding)
    """
    
    def __init__(self):
        super().__init__()
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default hallucination prevention rules."""
        
        # Rule: No assumption about unverified experience
        self.register_rule(Rule(
            id="no_unverified_assumption",
            name="No Unverified Assumption",
            description="Never assume candidate experience not explicitly verified in profile or conversation",
            rule_type=RuleType.HALLUCINATION,
            severity=RuleSeverity.BLOCKER,
            metadata={
                "check_against": ["verified_profile", "conversation_history"]
            }
        ))
        
        # Rule: Clarification required for vague claims
        self.register_rule(Rule(
            id="clarification_required",
            name="Clarification Required",
            description="If candidate vaguely references experience, ask clarification before deeper questioning",
            rule_type=RuleType.HALLUCINATION,
            severity=RuleSeverity.WARNING,
            metadata={
                "vague_indicators": ["worked on", "familiar with", "have experience", "used before"]
            }
        ))
        
        # Rule: No invented project details
        self.register_rule(Rule(
            id="no_invented_projects",
            name="No Invented Projects",
            description="Never reference specific project details not mentioned by candidate",
            rule_type=RuleType.HALLUCINATION,
            severity=RuleSeverity.BLOCKER,
            metadata={}
        ))
        
        # Rule: No assumed tech stack
        self.register_rule(Rule(
            id="no_assumed_tech_stack",
            name="No Assumed Tech Stack",
            description="Never assume technologies used unless explicitly stated",
            rule_type=RuleType.HALLUCINATION,
            severity=RuleSeverity.BLOCKER,
            metadata={}
        ))
        
        # Rule: Grounded knowledge only
        self.register_rule(Rule(
            id="grounded_knowledge_only",
            name="Grounded Knowledge Only",
            description="All technical claims must be grounded in retrieved knowledge or general facts",
            rule_type=RuleType.HALLUCINATION,
            severity=RuleSeverity.WARNING,
            metadata={}
        ))
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Evaluate a hallucination rule against context."""
        self._rule_execution_count[rule.id] += 1
        
        if rule.id == "no_unverified_assumption":
            return self._check_unverified_assumption(rule, context)
        elif rule.id == "clarification_required":
            return self._check_clarification_required(rule, context)
        elif rule.id == "no_invented_projects":
            return self._check_invented_projects(rule, context)
        elif rule.id == "no_assumed_tech_stack":
            return self._check_assumed_tech_stack(rule, context)
        elif rule.id == "grounded_knowledge_only":
            return self._check_grounded_knowledge(rule, context)
        else:
            return super().evaluate_rule(rule, context)
    
    def _check_unverified_assumption(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if generated question assumes unverified candidate experience.
        
        Context should contain:
        - generated_question: str
        - verified_profile: dict
        - conversation_history: list
        """
        generated_question = context.get("generated_question", "")
        verified_profile = context.get("verified_profile", {})
        conversation_history = context.get("conversation_history", [])
        
        # Extract entities mentioned in question
        mentioned_entities = self._extract_entities(generated_question)
        
        # Check if entities are verified
        unverified_entities = []
        for entity in mentioned_entities:
            if not self._is_entity_verified(entity, verified_profile, conversation_history):
                unverified_entities.append(entity)
        
        if unverified_entities:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Question assumes unverified entities: {', '.join(unverified_entities)}",
                context={"unverified_entities": unverified_entities}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="All mentioned entities are verified",
            context={}
        )
    
    def _check_clarification_required(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """
        Check if candidate's last response was vague and requires clarification.
        
        Context should contain:
        - candidate_last_response: str
        - generated_followup: str
        """
        candidate_response = context.get("candidate_last_response", "")
        generated_followup = context.get("generated_followup", "")
        
        vague_indicators = rule.metadata.get("vague_indicators", [])
        
        # Check if candidate response contains vague indicators
        is_vague = any(indicator in candidate_response.lower() for indicator in vague_indicators)
        
        # Check if followup asks for clarification
        clarification_patterns = [
            r"can you (tell me more|elaborate|explain)",
            r"what (exactly|specifically)",
            r"could you (clarify|provide more details)",
            r"how (did you|would you|do you)"
        ]
        asks_clarification = any(
            re.search(pattern, generated_followup.lower()) 
            for pattern in clarification_patterns
        )
        
        if is_vague and not asks_clarification:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason="Candidate response was vague, but followup doesn't ask for clarification",
                context={"candidate_response": candidate_response[:100]}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Clarification handling is appropriate",
            context={}
        )
    
    def _check_invented_projects(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Check if question references specific project details not mentioned."""
        generated_question = context.get("generated_question", "")
        verified_profile = context.get("verified_profile", {})
        conversation_history = context.get("conversation_history", [])
        
        # Look for specific project references in question
        project_patterns = [
            r"in your (\w+) project",
            r"when you built (\w+)",
            r"your (\w+) system",
            r"the (\w+) feature you mentioned"
        ]
        
        mentioned_projects = []
        for pattern in project_patterns:
            matches = re.findall(pattern, generated_question.lower())
            mentioned_projects.extend(matches)
        
        if not mentioned_projects:
            return RuleViolation(rule=rule, violated=False, reason="No specific projects referenced", context={})
        
        # Check if projects are verified
        verified_projects = self._extract_verified_projects(verified_profile, conversation_history)
        unverified_projects = [p for p in mentioned_projects if p not in verified_projects]
        
        if unverified_projects:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Question references unverified projects: {', '.join(unverified_projects)}",
                context={"unverified_projects": unverified_projects}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="All project references are verified",
            context={}
        )
    
    def _check_assumed_tech_stack(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Check if question assumes technologies not explicitly mentioned."""
        generated_question = context.get("generated_question", "")
        verified_profile = context.get("verified_profile", {})
        conversation_history = context.get("conversation_history", [])
        
        # Extract technology mentions
        tech_patterns = [
            r"\b(React|Angular|Vue|Node|Python|Java|AWS|Docker|Kubernetes|Redis|PostgreSQL)\b",
            r"using (\w+)",
            r"with (\w+)",
        ]
        
        mentioned_techs = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, generated_question, re.IGNORECASE)
            mentioned_techs.update(m.lower() for m in matches)
        
        if not mentioned_techs:
            return RuleViolation(rule=rule, violated=False, reason="No specific technologies referenced", context={})
        
        # Check if technologies are verified
        verified_techs = self._extract_verified_technologies(verified_profile, conversation_history)
        unverified_techs = [t for t in mentioned_techs if t not in verified_techs]
        
        if unverified_techs:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Question assumes unverified technologies: {', '.join(unverified_techs)}",
                context={"unverified_techs": unverified_techs}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="All technology references are verified",
            context={}
        )
    
    def _check_grounded_knowledge(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Check if technical claims are grounded in retrieved knowledge."""
        generated_question = context.get("generated_question", "")
        retrieved_context = context.get("retrieved_context", [])
        
        # If no retrieved context, this is likely a general question
        if not retrieved_context:
            return RuleViolation(
                rule=rule,
                violated=False,
                reason="No specific retrieved context required",
                context={}
            )
        
        # TODO: Implement more sophisticated grounding check
        # For now, just ensure retrieved context exists
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Retrieved context available for grounding",
            context={"retrieved_chunks": len(retrieved_context)}
        )
    
    # Helper methods
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential entities (projects, companies, technologies) from text."""
        # Simplified entity extraction - in production, use NER
        entities = []
        
        # Look for capitalized words (potential entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized)
        
        return list(set(entities))
    
    def _is_entity_verified(self, entity: str, verified_profile: Dict, conversation_history: List) -> bool:
        """Check if an entity is verified in profile or conversation."""
        # Check profile
        profile_text = str(verified_profile).lower()
        if entity.lower() in profile_text:
            return True
        
        # Check conversation history
        for turn in conversation_history:
            if entity.lower() in str(turn).lower():
                return True
        
        return False
    
    def _extract_verified_projects(self, verified_profile: Dict, conversation_history: List) -> List[str]:
        """Extract verified project names from profile and conversation."""
        projects = []
        
        # Extract from profile
        if "projects" in verified_profile:
            for project in verified_profile.get("projects", []):
                if isinstance(project, dict):
                    projects.append(project.get("name", "").lower())
                else:
                    projects.append(str(project).lower())
        
        # Extract from conversation (simplified)
        for turn in conversation_history:
            content = str(turn).lower()
            # Look for "I worked on X" patterns
            matches = re.findall(r"worked on (\w+)", content)
            projects.extend(matches)
        
        return list(set(projects))
    
    def _extract_verified_technologies(self, verified_profile: Dict, conversation_history: List) -> List[str]:
        """Extract verified technologies from profile and conversation."""
        techs = []
        
        # Extract from profile
        if "skills" in verified_profile:
            techs.extend([s.lower() for s in verified_profile.get("skills", [])])
        if "technologies" in verified_profile:
            techs.extend([t.lower() for t in verified_profile.get("technologies", [])])
        
        # Extract from conversation
        for turn in conversation_history:
            content = str(turn).lower()
            # Common tech pattern matches
            tech_names = re.findall(
                r'\b(react|angular|vue|node|python|java|aws|docker|kubernetes|redis|postgresql|mongodb|express|django|flask|spring)\b',
                content,
                re.IGNORECASE
            )
            techs.extend([t.lower() for t in tech_names])
        
        return list(set(techs))
