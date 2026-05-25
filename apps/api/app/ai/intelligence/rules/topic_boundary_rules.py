"""
Topic Boundary Rules Engine.

Prevents interview domain drift:
- Frontend interviews staying in frontend domain
- Backend interviews not drifting to system design (unless configured)
- Behavioral interviews maintaining behavioral focus
- Scope boundaries enforced by configuration
"""
from typing import Dict, List, Any, Set
import logging

from app.ai.intelligence.rules.rule_engine import (
    RuleEngine, Rule, RuleType, RuleSeverity, RuleViolation
)

logger = logging.getLogger(__name__)


# Domain keyword mappings
DOMAIN_KEYWORDS = {
    "frontend": {
        "react", "vue", "angular", "css", "html", "javascript", "typescript",
        "dom", "browser", "webpack", "responsive", "accessibility", "components",
        "hooks", "state management", "redux", "mobx", "ui", "ux"
    },
    "backend": {
        "api", "rest", "graphql", "database", "sql", "orm", "authentication",
        "authorization", "server", "nodejs", "python", "java", "ruby", "go",
        "microservices", "caching", "queue", "worker", "background jobs"
    },
    "system_design": {
        "scalability", "distributed", "load balancer", "sharding", "partitioning",
        "consistency", "availability", "cap theorem", "consensus", "replication",
        "caching strategy", "cdn", "microservices architecture", "event sourcing",
        "message queue", "kafka", "rabbitmq", "elasticsearch"
    },
    "behavioral": {
        "leadership", "conflict", "team", "project", "challenge", "difficult",
        "success", "failure", "decision", "prioritize", "communicate", "feedback",
        "star method", "situation", "task", "action", "result", "ownership"
    },
    "data_structures": {
        "array", "linked list", "tree", "graph", "hash", "heap", "stack", "queue",
        "sorting", "searching", "dynamic programming", "recursion", "complexity",
        "big o", "algorithm", "binary search", "dfs", "bfs"
    },
}


class TopicBoundaryRuleEngine(RuleEngine):
    """
    Specialized rule engine for enforcing topic boundaries.
    
    Prevents domain drift during interviews by validating that
    questions and follow-ups stay within the configured scope.
    """
    
    def __init__(self):
        super().__init__()
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default topic boundary rules."""
        
        # Rule: Frontend scope only
        self.register_rule(Rule(
            id="frontend_scope_only",
            name="Frontend Scope Only",
            description="Frontend interviews must not drift into backend or distributed systems",
            rule_type=RuleType.TOPIC_BOUNDARY,
            severity=RuleSeverity.BLOCKER,
            metadata={
                "allowed_domains": ["frontend"],
                "forbidden_domains": ["backend", "system_design", "data_structures"]
            }
        ))
        
        # Rule: Backend scope only
        self.register_rule(Rule(
            id="backend_scope_only",
            name="Backend Scope Only",
            description="Backend interviews must not drift into frontend specifics",
            rule_type=RuleType.TOPIC_BOUNDARY,
            severity=RuleSeverity.BLOCKER,
            metadata={
                "allowed_domains": ["backend"],
                "forbidden_domains": ["frontend"],
                "warning_domains": ["system_design"]  # Warning, not blocker
            }
        ))
        
        # Rule: Behavioral scope only
        self.register_rule(Rule(
            id="behavioral_scope_only",
            name="Behavioral Scope Only",
            description="Behavioral interviews must focus on experiences, not technical implementation",
            rule_type=RuleType.TOPIC_BOUNDARY,
            severity=RuleSeverity.BLOCKER,
            metadata={
                "allowed_domains": ["behavioral"],
                "forbidden_domains": ["frontend", "backend", "system_design", "data_structures"]
            }
        ))
        
        # Rule: System design scope controlled
        self.register_rule(Rule(
            id="system_design_scope_controlled",
            name="System Design Scope Controlled",
            description="System design interviews should stay at architecture level, not implementation details",
            rule_type=RuleType.TOPIC_BOUNDARY,
            severity=RuleSeverity.WARNING,
            metadata={
                "allowed_domains": ["system_design", "backend"],
                "forbidden_domains": ["frontend", "data_structures"]
            }
        ))
        
        # Rule: No coding in behavioral rounds
        self.register_rule(Rule(
            id="no_coding_in_behavioral",
            name="No Coding in Behavioral",
            description="Behavioral rounds should not ask for code or technical implementation",
            rule_type=RuleType.TOPIC_BOUNDARY,
            severity=RuleSeverity.BLOCKER,
            metadata={}
        ))
        
        # Rule: Topic consistency
        self.register_rule(Rule(
            id="topic_consistency",
            name="Topic Consistency",
            description="Questions should maintain consistency with interview configuration",
            rule_type=RuleType.TOPIC_BOUNDARY,
            severity=RuleSeverity.WARNING,
            metadata={}
        ))
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Evaluate a topic boundary rule against context."""
        self._rule_execution_count[rule.id] += 1
        
        if rule.id == "frontend_scope_only":
            return self._check_domain_scope(rule, context, "frontend")
        elif rule.id == "backend_scope_only":
            return self._check_domain_scope(rule, context, "backend")
        elif rule.id == "behavioral_scope_only":
            return self._check_domain_scope(rule, context, "behavioral")
        elif rule.id == "system_design_scope_controlled":
            return self._check_domain_scope(rule, context, "system_design")
        elif rule.id == "no_coding_in_behavioral":
            return self._check_no_coding_in_behavioral(rule, context)
        elif rule.id == "topic_consistency":
            return self._check_topic_consistency(rule, context)
        else:
            return super().evaluate_rule(rule, context)
    
    def _check_domain_scope(self, rule: Rule, context: Dict[str, Any], expected_domain: str) -> RuleViolation:
        """
        Check if generated content stays within allowed domain scope.
        
        Context should contain:
        - generated_question: str
        - interview_config: dict (with domain, focus, etc.)
        """
        generated_question = context.get("generated_question", "")
        interview_config = context.get("interview_config", {})
        
        # Get configured domain
        configured_domain = interview_config.get("domain", "").lower()
        
        # Only apply rule if domain matches
        if configured_domain != expected_domain:
            return RuleViolation(
                rule=rule,
                violated=False,
                reason=f"Rule not applicable (configured domain: {configured_domain})",
                context={}
            )
        
        # Detect domains in question
        detected_domains = self._detect_domains(generated_question)
        
        allowed_domains = set(rule.metadata.get("allowed_domains", []))
        forbidden_domains = set(rule.metadata.get("forbidden_domains", []))
        warning_domains = set(rule.metadata.get("warning_domains", []))
        
        # Check for forbidden domains
        forbidden_detected = detected_domains & forbidden_domains
        if forbidden_detected:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Question contains forbidden domain keywords: {', '.join(forbidden_detected)}",
                context={
                    "detected_domains": list(detected_domains),
                    "forbidden_detected": list(forbidden_detected)
                }
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        # Check for warning domains
        warning_detected = detected_domains & warning_domains
        if warning_detected:
            return RuleViolation(
                rule=rule,
                violated=True,  # Violated but with WARNING severity
                reason=f"Question contains warning domain keywords: {', '.join(warning_detected)}",
                context={
                    "detected_domains": list(detected_domains),
                    "warning_detected": list(warning_detected)
                }
            )
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Question stays within allowed domain scope",
            context={"detected_domains": list(detected_domains)}
        )
    
    def _check_no_coding_in_behavioral(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Check if behavioral interview contains coding questions."""
        generated_question = context.get("generated_question", "")
        interview_config = context.get("interview_config", {})
        
        interview_type = interview_config.get("type", "").lower()
        
        # Only apply to behavioral interviews
        if interview_type != "behavioral":
            return RuleViolation(
                rule=rule,
                violated=False,
                reason="Rule not applicable (not a behavioral interview)",
                context={}
            )
        
        # Check for code-related keywords
        code_indicators = [
            "write code", "implement", "function", "algorithm", "syntax",
            "compile", "debug", "class", "variable", "loop", "if statement"
        ]
        
        question_lower = generated_question.lower()
        found_indicators = [ind for ind in code_indicators if ind in question_lower]
        
        if found_indicators:
            violation = RuleViolation(
                rule=rule,
                violated=True,
                reason=f"Behavioral interview contains coding keywords: {', '.join(found_indicators)}",
                context={"code_indicators": found_indicators}
            )
            self._rule_violation_count[rule.id] += 1
            return violation
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="No coding keywords detected in behavioral interview",
            context={}
        )
    
    def _check_topic_consistency(self, rule: Rule, context: Dict[str, Any]) -> RuleViolation:
        """Check if question is consistent with interview configuration."""
        generated_question = context.get("generated_question", "")
        interview_config = context.get("interview_config", {})
        
        configured_domain = interview_config.get("domain", "").lower()
        configured_focus = interview_config.get("focus", "").lower()
        
        if not configured_domain:
            return RuleViolation(
                rule=rule,
                violated=False,
                reason="No domain configured to check consistency",
                context={}
            )
        
        # Detect domains in question
        detected_domains = self._detect_domains(generated_question)
        
        # Check if primary detected domain matches configuration
        if configured_domain not in detected_domains and detected_domains:
            strongest_domain = self._get_strongest_domain(generated_question)
            
            if strongest_domain and strongest_domain != configured_domain:
                return RuleViolation(
                    rule=rule,
                    violated=True,
                    reason=f"Question domain ({strongest_domain}) doesn't match config ({configured_domain})",
                    context={
                        "configured_domain": configured_domain,
                        "detected_domain": strongest_domain,
                        "all_detected": list(detected_domains)
                    }
                )
        
        return RuleViolation(
            rule=rule,
            violated=False,
            reason="Question is consistent with interview configuration",
            context={"detected_domains": list(detected_domains)}
        )
    
    # Helper methods
    
    def _detect_domains(self, text: str) -> Set[str]:
        """Detect which domains are referenced in text."""
        text_lower = text.lower()
        detected = set()
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                detected.add(domain)
        
        return detected
    
    def _get_strongest_domain(self, text: str) -> str:
        """Get the domain with most keyword matches."""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            domain_scores[domain] = score
        
        if not domain_scores:
            return ""
        
        return max(domain_scores.items(), key=lambda x: x[1])[0]
    
    def get_domain_coverage(self, text: str) -> Dict[str, int]:
        """Get keyword coverage for each domain."""
        text_lower = text.lower()
        coverage = {}
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                coverage[domain] = matches
        
        return coverage
