import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.ai.voice.policies.domain_policy import InterviewDomain

logger = logging.getLogger("rubric_registry")

@dataclass
class RubricDimension:
    name: str
    weight: float
    criteria: str
    levels: Dict[int, Dict[str, str]]

@dataclass
class RubricDefinition:
    domain: InterviewDomain
    name: str
    dimensions: List[RubricDimension] = field(default_factory=list)


FRONTEND_RUBRIC = RubricDefinition(
    domain=InterviewDomain.FRONTEND,
    name="Frontend Engineering Interview",
    dimensions=[
        RubricDimension(
            name="FRONTEND_FUNDAMENTALS",
            weight=0.25,
            criteria="Rendering, hydration, SSR, browser APIs, DOM, event handling",
            levels={
                1: {"name": "Novice", "desc": "Unable to explain basic rendering or browser concepts"},
                2: {"name": "Aware", "desc": "Understands basic concepts but cannot explain tradeoffs"},
                3: {"name": "Proficient", "desc": "Explains rendering, hydration, and SSR with practical examples"},
                4: {"name": "Advanced", "desc": "Deep understanding of rendering optimization, hydration strategies, browser internals"},
                5: {"name": "Expert", "desc": "Architects frontend systems with optimal rendering, lazy loading, and performance budgets"},
            },
        ),
        RubricDimension(
            name="FRONTEND_ARCHITECTURE",
            weight=0.25,
            criteria="State management, component architecture, design systems, microfrontends",
            levels={
                1: {"name": "Novice", "desc": "No clear architecture understanding"},
                2: {"name": "Aware", "desc": "Knows patterns but cannot explain tradeoffs"},
                3: {"name": "Proficient", "desc": "Designs component hierarchies and state flows clearly"},
                4: {"name": "Advanced", "desc": "Microfrontend design, design system creation, complex state orchestration"},
                5: {"name": "Expert", "desc": "Enterprise-scale component architecture, cross-team design systems, module federation"},
            },
        ),
        RubricDimension(
            name="PERFORMANCE",
            weight=0.20,
            criteria="Bundle optimization, caching, CDN, web vitals, asset optimization",
            levels={
                1: {"name": "Novice", "desc": "No performance awareness"},
                2: {"name": "Aware", "desc": "Knows performance matters but cannot identify bottlenecks"},
                3: {"name": "Proficient", "desc": "Uses web vitals, code splitting, and caching effectively"},
                4: {"name": "Advanced", "desc": "Performance budgets, RUM, advanced caching strategies, CDN optimization"},
                5: {"name": "Expert", "desc": "Custom performance tooling, critical path optimization, real user monitoring at scale"},
            },
        ),
        RubricDimension(
            name="TOOLS_AND_BUILD",
            weight=0.15,
            criteria="Build tools, testing, TypeScript, accessibility, CI/CD for frontend",
            levels={
                1: {"name": "Novice", "desc": "Basic tool usage only"},
                2: {"name": "Aware", "desc": "Knows build tools but cannot configure them"},
                3: {"name": "Proficient", "desc": "Configures build pipelines, testing, and TypeScript effectively"},
                4: {"name": "Advanced", "desc": "Custom build configurations, a11y expertise, comprehensive testing strategies"},
                5: {"name": "Expert", "desc": "Build system design, monorepo management, test infrastructure, accessibility audits"},
            },
        ),
        RubricDimension(
            name="COMMUNICATION",
            weight=0.15,
            criteria="Clarity, structure, frontend vocabulary, tradeoff articulation",
            levels={
                1: {"name": "Unclear", "desc": "Difficult to follow, poor vocabulary"},
                2: {"name": "Basic", "desc": "Coherent but lacks precision"},
                3: {"name": "Clear", "desc": "Good technical communication with examples"},
                4: {"name": "Precise", "desc": "Excellent tradeoff articulation and technical depth"},
                5: {"name": "Eloquent", "desc": "Masterful explanations with analogies and precision"},
            },
        ),
    ],
)

BACKEND_RUBRIC = RubricDefinition(
    domain=InterviewDomain.BACKEND,
    name="Backend Engineering Interview",
    dimensions=[
        RubricDimension(
            name="SYSTEMS_AND_ARCHITECTURE",
            weight=0.25,
            criteria="API design, microservices, event-driven architecture, distributed systems",
            levels={
                1: {"name": "Novice", "desc": "Monolithic thinking, no service decomposition"},
                2: {"name": "Aware", "desc": "Understands REST/services but not tradeoffs"},
                3: {"name": "Proficient", "desc": "Designs clear APIs, understands sync vs async patterns"},
                4: {"name": "Advanced", "desc": "Event-driven design, CQRS, saga patterns, distributed consistency"},
                5: {"name": "Expert", "desc": "Designs complex distributed systems with clear tradeoff analysis"},
            },
        ),
        RubricDimension(
            name="DATA_AND_STORAGE",
            weight=0.25,
            criteria="Database design, SQL/NoSQL tradeoffs, indexing, caching, data modeling",
            levels={
                1: {"name": "Novice", "desc": "Basic CRUD, no optimization awareness"},
                2: {"name": "Aware", "desc": "Knows indexes exist but cannot explain types"},
                3: {"name": "Proficient", "desc": "Schema design, query optimization, cache strategies"},
                4: {"name": "Advanced", "desc": "Complex data modeling, partitioning, replication strategies"},
                5: {"name": "Expert", "desc": "Multi-model database design, custom cache layers, data pipeline architecture"},
            },
        ),
        RubricDimension(
            name="PERFORMANCE_AND_SCALING",
            weight=0.20,
            criteria="Horizontal/vertical scaling, load balancing, profiling, bottlenecks",
            levels={
                1: {"name": "Novice", "desc": "No scaling awareness"},
                2: {"name": "Aware", "desc": "Knows scaling concepts but cannot apply"},
                3: {"name": "Proficient", "desc": "Identifies bottlenecks, applies caching, understands scaling patterns"},
                4: {"name": "Advanced", "desc": "Performance profiling, capacity planning, auto-scaling design"},
                5: {"name": "Expert", "desc": "System-wide performance optimization, cost-performance modeling"},
            },
        ),
        RubricDimension(
            name="RELIABILITY",
            weight=0.15,
            criteria="Error handling, testing, monitoring, observability, fault tolerance",
            levels={
                1: {"name": "Novice", "desc": "Basic error handling only"},
                2: {"name": "Aware", "desc": "Knows testing types but shallow coverage"},
                3: {"name": "Proficient", "desc": "Comprehensive testing, monitoring, graceful error handling"},
                4: {"name": "Advanced", "desc": "Observability pipelines, chaos engineering, SLA design"},
                5: {"name": "Expert", "desc": "Production-grade reliability patterns, incident response systems"},
            },
        ),
        RubricDimension(
            name="COMMUNICATION",
            weight=0.15,
            criteria="Clarity, structure, backend vocabulary, tradeoff articulation",
            levels={
                1: {"name": "Unclear", "desc": "Difficult to follow, poor vocabulary"},
                2: {"name": "Basic", "desc": "Coherent but lacks precision"},
                3: {"name": "Clear", "desc": "Good technical communication with examples"},
                4: {"name": "Precise", "desc": "Excellent tradeoff articulation and technical depth"},
                5: {"name": "Eloquent", "desc": "Masterful explanations with analogies and precision"},
            },
        ),
    ],
)

SYSTEM_DESIGN_RUBRIC = RubricDefinition(
    domain=InterviewDomain.SYSTEM_DESIGN_BACKEND,
    name="System Design Interview",
    dimensions=[
        RubricDimension(
            name="REQUIREMENTS_CLARIFICATION",
            weight=0.20,
            criteria="Requirements gathering, scope definition, constraints identification",
            levels={
                1: {"name": "Jumps to solution", "desc": "No requirements asked, immediate solution"},
                2: {"name": "Basic", "desc": "Asks some questions but misses key constraints"},
                3: {"name": "Thorough", "desc": "Systematic requirements gathering with functional/non-functional split"},
                4: {"name": "Comprehensive", "desc": "Deep requirements analysis with tradeoff framing"},
                5: {"name": "Masterful", "desc": "Exhaustive scope definition with prioritization and future-proofing"},
            },
        ),
        RubricDimension(
            name="HIGH_LEVEL_DESIGN",
            weight=0.20,
            criteria="System decomposition, component identification, data flow",
            levels={
                1: {"name": "Unstructured", "desc": "No clear system decomposition"},
                2: {"name": "Basic", "desc": "Simple components but missing key elements"},
                3: {"name": "Structured", "desc": "Clear component diagram with data flow"},
                4: {"name": "Detailed", "desc": "Well-structured design with API contracts and interfaces"},
                5: {"name": "Architectural", "desc": "Clean architecture with clear separation of concerns"},
            },
        ),
        RubricDimension(
            name="DEEP_DIVE",
            weight=0.20,
            criteria="Data model, API design, key algorithm, bottleneck analysis",
            levels={
                1: {"name": "Shallow", "desc": "No deep dive into any component"},
                2: {"name": "Surface", "desc": "Covers surface-level details only"},
                3: {"name": "Detailed", "desc": "Deep dive into 1-2 critical components"},
                4: {"name": "Comprehensive", "desc": "Thorough analysis of all critical paths"},
                5: {"name": "Exhaustive", "desc": "Complete deep dive with quantitative reasoning"},
            },
        ),
        RubricDimension(
            name="SCALABILITY",
            weight=0.20,
            criteria="Scaling strategy, bottlenecks, tradeoffs, caching, partitioning",
            levels={
                1: {"name": "None", "desc": "No scalability considerations"},
                2: {"name": "Basic", "desc": "Mentions scaling but vague"},
                3: {"name": "Practical", "desc": "Clear scaling strategy with identified bottlenecks"},
                4: {"name": "Advanced", "desc": "Detailed tradeoff analysis, multiple scaling dimensions"},
                5: {"name": "Comprehensive", "desc": "Quantitative scaling model, cost-performance analysis"},
            },
        ),
        RubricDimension(
            name="COMMUNICATION",
            weight=0.20,
            criteria="Clarity, structure, system design vocabulary, tradeoff articulation",
            levels={
                1: {"name": "Unclear", "desc": "Difficult to follow, no structure"},
                2: {"name": "Basic", "desc": "Coherent but lacks systematic approach"},
                3: {"name": "Structured", "desc": "Clear progression from requirements to design"},
                4: {"name": "Engaging", "desc": "Interactive interview, checks in with interviewer"},
                5: {"name": "Masterful", "desc": "Perfect structure, tradeoff-first thinking, whiteboard-quality communication"},
            },
        ),
    ],
)

GENERAL_RUBRIC = RubricDefinition(
    domain=InterviewDomain.GENERAL,
    name="General Technical Interview",
    dimensions=[
        RubricDimension(
            name="TECHNICAL_DEPTH",
            weight=0.35,
            criteria="Conceptual understanding, problem-solving, tradeoff reasoning",
            levels={
                1: {"name": "Shallow", "desc": "Lacks conceptual clarity or simple correctness"},
                2: {"name": "Moderate", "desc": "Explains basics but misses depth or edge cases"},
                3: {"name": "Strong", "desc": "Thorough understanding with practical examples"},
                4: {"name": "Advanced", "desc": "Deep tradeoff reasoning under constraints"},
                5: {"name": "Expert", "desc": "Novel insights, quantitative reasoning, production awareness"},
            },
        ),
        RubricDimension(
            name="COMMUNICATION",
            weight=0.25,
            criteria="Clarity, structure, vocabulary, articulation",
            levels={
                1: {"name": "Unclear", "desc": "Difficult to follow, poor vocabulary"},
                2: {"name": "Basic", "desc": "Coherent but lacks precision or structure"},
                3: {"name": "Clear", "desc": "Structured communication with examples"},
                4: {"name": "Precise", "desc": "Excellent articulation with tradeoff analysis"},
                5: {"name": "Eloquent", "desc": "Masterful explanations with analogies and precision"},
            },
        ),
        RubricDimension(
            name="BEHAVIORAL",
            weight=0.20,
            criteria="Confidence, hesitation recovery, adaptability",
            levels={
                1: {"name": "Fragile", "desc": "Frequent long pauses, collapses under pressure"},
                2: {"name": "Hesitant", "desc": "Occasional pauses, recovers with assistance"},
                3: {"name": "Steady", "desc": "Stable delivery, handles interruptions cleanly"},
                4: {"name": "Adaptable", "desc": "Incorporates hints, recalibrates on-the-fly"},
                5: {"name": "Resilient", "desc": "Absolute composure under high stress"},
            },
        ),
        RubricDimension(
            name="PROBLEM_SOLVING",
            weight=0.20,
            criteria="Approach structure, edge case handling, systematic thinking",
            levels={
                1: {"name": "Unstructured", "desc": "Random approach, no methodology"},
                2: {"name": "Basic", "desc": "Linear approach but misses edge cases"},
                3: {"name": "Systematic", "desc": "Clear methodology with edge cases considered"},
                4: {"name": "Rigorous", "desc": "Exhaustive analysis, multiple solution paths"},
                5: {"name": "Masterful", "desc": "Elegant solutions with optimal tradeoffs"},
            },
        ),
    ],
)


class RubricRegistry:
    def __init__(self):
        self._rubrics: Dict[InterviewDomain, RubricDefinition] = {
            InterviewDomain.FRONTEND: FRONTEND_RUBRIC,
            InterviewDomain.SYSTEM_DESIGN_FRONTEND: FRONTEND_RUBRIC,
            InterviewDomain.BACKEND: BACKEND_RUBRIC,
            InterviewDomain.SYSTEM_DESIGN_BACKEND: SYSTEM_DESIGN_RUBRIC,
            InterviewDomain.FULLSTACK: BACKEND_RUBRIC,
            InterviewDomain.AI_ENGINEERING: BACKEND_RUBRIC,
        }

    def get_rubric(self, domain: InterviewDomain) -> Optional[RubricDefinition]:
        return self._rubrics.get(domain)

    def register_rubric(self, domain: InterviewDomain, rubric: RubricDefinition) -> None:
        self._rubrics[domain] = rubric
        logger.info("rubric_registered | domain: %s | rubric: %s", domain.value, rubric.name)
