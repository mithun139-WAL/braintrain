import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger("domain_policy")

class InterviewDomain(str, Enum):
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    FULLSTACK = "FULLSTACK"
    AI_ENGINEERING = "AI_ENGINEERING"
    DEVOPS = "DEVOPS"
    MOBILE = "MOBILE"
    SYSTEM_DESIGN_FRONTEND = "SYSTEM_DESIGN_FRONTEND"
    SYSTEM_DESIGN_BACKEND = "SYSTEM_DESIGN_BACKEND"
    BEHAVIORAL = "BEHAVIORAL"
    GENERAL = "GENERAL"

FRONTEND_ALLOWED_TOPICS = [
    "SSR", "hydration", "rendering", "browser performance",
    "bundle optimization", "React architecture", "frontend caching",
    "state management", "design systems", "accessibility",
    "CDN usage", "microfrontends", "asset optimization",
    "virtual DOM", "tree shaking", "code splitting",
    "lazy loading", "progressive enhancement", "CSS architecture",
    "responsive design", "web vitals", "client-side routing",
    "server-side rendering", "static site generation", "web workers",
    "service workers", "PWA", "cross-browser compatibility",
    "component lifecycle", "hooks", "context API", "Redux",
    "TypeScript", "build tools", "webpack", "vite", "esbuild",
    "testing (unit/integration/e2e)", "component testing",
    "storybook", "style systems", "CSS-in-JS", "TailwindCSS",
    "SEO", "performance monitoring", "Real User Monitoring (RUM)",
]

FRONTEND_RESTRICTED_TOPICS = [
    "distributed consensus", "Kafka internals", "database replication",
    "Raft/Paxos", "sharding", "leader election", "backend scaling",
    "distributed transactions", "two-phase commit", "saga patterns",
    "consensus algorithms", "vector clocks", "gossip protocol",
    "distributed file systems", "block storage", "HDFS internals",
    "database indexing internals", "query optimization (backend)",
    "backend load balancing strategies", "backend service mesh",
    "API gateway internals", "circuit breaker internals",
    "rate limiting algorithms", "distributed caching coherence",
]

BACKEND_ALLOWED_TOPICS = [
    "API design", "REST", "GraphQL", "gRPC", "database design",
    "SQL", "NoSQL", "indexing", "query optimization", "caching",
    "distributed systems", "microservices", "message queues",
    "event-driven architecture", "authentication", "authorization",
    "rate limiting", "load balancing", "horizontal scaling",
    "vertical scaling", "database replication", "sharding",
    "CAP theorem", "consistency models", "idempotency",
    "background jobs", "cron", "WebSocket", "real-time systems",
    "monitoring", "observability", "logging", "tracing",
    "CI/CD", "testing strategies", "error handling",
    "data modeling", "migrations", "API versioning",
    "rate limiting", "throttling", "DDoS protection",
    "containerization", "Docker", "Kubernetes",
]

BACKEND_RESTRICTED_TOPICS: List[str] = []


@dataclass
class DomainContext:
    primary_domain: InterviewDomain
    allowed_topics: List[str] = field(default_factory=list)
    restricted_topics: List[str] = field(default_factory=list)
    subdomain: str = ""

    def __post_init__(self):
        if not self.allowed_topics:
            self.allowed_topics = get_allowed_topics(self.primary_domain)
        if not self.restricted_topics:
            self.restricted_topics = get_restricted_topics(self.primary_domain)

    def allows_topic(self, topic: str) -> bool:
        topic_lower = topic.lower()
        for restricted in self.restricted_topics:
            if restricted.lower() in topic_lower:
                logger.warning("domain_policy | restricted topic '%s' blocked in domain %s", topic, self.primary_domain.value)
                return False
        if not self.allowed_topics:
            return True
        for allowed in self.allowed_topics:
            if allowed.lower() in topic_lower:
                return True
        return True

    def is_topic_restricted(self, topic: str) -> bool:
        topic_lower = topic.lower()
        for restricted in self.restricted_topics:
            if restricted.lower() in topic_lower:
                return True
        return False

    def format_domain_instructions(self) -> str:
        allowed = ", ".join(self.allowed_topics) if self.allowed_topics else "general scope"
        restricted = ", ".join(self.restricted_topics) if self.restricted_topics else "none"

        return (
            f"[DOMAIN CONTEXT: {self.primary_domain.value}]\n"
            f"Allowed topics: {allowed}\n"
            f"Restricted topics: {restricted}\n"
            "All questions and followups MUST remain inside the selected interview domain "
            "unless the candidate explicitly requests a different scope.\n"
            "Do NOT drift into restricted topics even if the candidate mentions related keywords."
        )


class DomainPolicy:
    def __init__(self):
        self._domain_map: dict[str, InterviewDomain] = {
            "frontend": InterviewDomain.FRONTEND,
            "backend": InterviewDomain.BACKEND,
            "fullstack": InterviewDomain.FULLSTACK,
            "ai": InterviewDomain.AI_ENGINEERING,
            "ai/ml": InterviewDomain.AI_ENGINEERING,
            "machine learning": InterviewDomain.AI_ENGINEERING,
            "devops": InterviewDomain.DEVOPS,
            "mobile": InterviewDomain.MOBILE,
            "system design frontend": InterviewDomain.SYSTEM_DESIGN_FRONTEND,
            "system design backend": InterviewDomain.SYSTEM_DESIGN_BACKEND,
            "behavioral": InterviewDomain.BEHAVIORAL,
        }

    def resolve_domain(self, topic: str) -> InterviewDomain:
        topic_lower = topic.lower().strip()
        for key, domain in self._domain_map.items():
            if key in topic_lower:
                return domain
        return InterviewDomain.GENERAL

    def create_context(self, topic: str, subdomain: str = "") -> DomainContext:
        domain = self.resolve_domain(topic)
        return DomainContext(
            primary_domain=domain,
            subdomain=subdomain,
        )

    def validate_question_domain(self, question_text: str, domain_context: DomainContext) -> bool:
        return domain_context.allows_topic(question_text)

    def get_domain_restriction(self, domain: InterviewDomain) -> Optional[str]:
        restrictions = {
            InterviewDomain.FRONTEND: "Do NOT ask backend distributed systems questions (Kafka, sharding, replication, consensus algorithms, leader election, database partitioning).",
            InterviewDomain.SYSTEM_DESIGN_FRONTEND: "Do NOT ask backend system design questions. Focus on frontend architecture, rendering, state management, and browser performance.",
            InterviewDomain.AI_ENGINEERING: "Do NOT ask general backend or infrastructure questions unless directly related to AI/ML systems.",
        }
        return restrictions.get(domain)


def get_allowed_topics(domain: InterviewDomain) -> List[str]:
    mapping = {
        InterviewDomain.FRONTEND: FRONTEND_ALLOWED_TOPICS,
        InterviewDomain.SYSTEM_DESIGN_FRONTEND: FRONTEND_ALLOWED_TOPICS,
        InterviewDomain.BACKEND: BACKEND_ALLOWED_TOPICS,
        InterviewDomain.SYSTEM_DESIGN_BACKEND: BACKEND_ALLOWED_TOPICS,
        InterviewDomain.FULLSTACK: FRONTEND_ALLOWED_TOPICS + BACKEND_ALLOWED_TOPICS,
        InterviewDomain.AI_ENGINEERING: BACKEND_ALLOWED_TOPICS + [
            "LLM", "RAG", "embeddings", "vector databases", "prompt engineering",
            "fine-tuning", "model deployment", "inference optimization",
            "training pipelines", "evaluation", "agents", "tool use",
        ],
    }
    return mapping.get(domain, [])


def get_restricted_topics(domain: InterviewDomain) -> List[str]:
    mapping = {
        InterviewDomain.FRONTEND: FRONTEND_RESTRICTED_TOPICS,
        InterviewDomain.SYSTEM_DESIGN_FRONTEND: FRONTEND_RESTRICTED_TOPICS,
        InterviewDomain.BACKEND: BACKEND_RESTRICTED_TOPICS,
    }
    return mapping.get(domain, [])
