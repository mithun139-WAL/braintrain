"""Seed global topics

Revision ID: 0003_seed_global_topics
Revises: 0002_schema_fix
Create Date: 2026-05-19

Inserts the curated set of global interview-prep topics.
All topics are is_global=TRUE and created_by_user_id=NULL.

Hierarchy:
  Technical Skills  (parent)
    ├─ Data Structures & Algorithms
    ├─ System Design
    ├─ Database Design
    ├─ Frontend Development
    ├─ Backend Development
    ├─ DevOps & Cloud
    └─ Machine Learning & AI
  Behavioral Skills  (parent)
    ├─ Leadership & Teamwork
    ├─ Problem Solving & Decision Making
    └─ Communication & Presentation
  Domain Expertise  (parent)
    ├─ API Design & Architecture
    ├─ Security & Authentication
    └─ Mobile Development

UUIDs are fixed so the seed is idempotent when re-run against a fresh DB.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_seed_global_topics"
down_revision: Union[str, None] = "0002_schema_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Fixed UUIDs (deterministic, never change) ─────────────────────────────────
_P1 = "00000000-0000-0000-0000-000000000001"  # Technical Skills
_P2 = "00000000-0000-0000-0000-000000000002"  # Behavioral Skills
_P3 = "00000000-0000-0000-0000-000000000003"  # Domain Expertise

_T1 = "00000000-0000-0000-0000-000000000011"  # Data Structures & Algorithms
_T2 = "00000000-0000-0000-0000-000000000012"  # System Design
_T3 = "00000000-0000-0000-0000-000000000013"  # Database Design
_T4 = "00000000-0000-0000-0000-000000000014"  # Frontend Development
_T5 = "00000000-0000-0000-0000-000000000015"  # Backend Development
_T6 = "00000000-0000-0000-0000-000000000016"  # DevOps & Cloud
_T7 = "00000000-0000-0000-0000-000000000017"  # Machine Learning & AI

_B1 = "00000000-0000-0000-0000-000000000021"  # Leadership & Teamwork
_B2 = "00000000-0000-0000-0000-000000000022"  # Problem Solving & Decision Making
_B3 = "00000000-0000-0000-0000-000000000023"  # Communication & Presentation

_D1 = "00000000-0000-0000-0000-000000000031"  # API Design & Architecture
_D2 = "00000000-0000-0000-0000-000000000032"  # Security & Authentication
_D3 = "00000000-0000-0000-0000-000000000033"  # Mobile Development


def upgrade() -> None:
    # Insert parents first (no parent_topic_id)
    _insert_topics([
        dict(
            id=_P1,
            name="Technical Skills",
            description=(
                "Core computer science and engineering concepts tested in "
                "technical interviews — algorithms, system design, databases, "
                "and modern engineering disciplines."
            ),
            parent_topic_id=None,
        ),
        dict(
            id=_P2,
            name="Behavioral Skills",
            description=(
                "Soft-skill and situational interview questions that assess "
                "leadership, communication, problem-solving, and cultural fit."
            ),
            parent_topic_id=None,
        ),
        dict(
            id=_P3,
            name="Domain Expertise",
            description=(
                "Specialised technical domains including API design, security "
                "engineering, and mobile development."
            ),
            parent_topic_id=None,
        ),
    ])

    # Insert children
    _insert_topics([
        # ── Technical Skills children ─────────────────────────────────────────
        dict(
            id=_T1,
            name="Data Structures & Algorithms",
            description=(
                "Arrays, linked lists, trees, graphs, sorting, searching, "
                "dynamic programming, and Big-O complexity analysis."
            ),
            parent_topic_id=_P1,
        ),
        dict(
            id=_T2,
            name="System Design",
            description=(
                "Scalable distributed systems — load balancers, caching, "
                "message queues, microservices, CAP theorem, and capacity planning."
            ),
            parent_topic_id=_P1,
        ),
        dict(
            id=_T3,
            name="Database Design",
            description=(
                "Relational and NoSQL database modelling, query optimisation, "
                "indexing strategies, transactions, and ACID vs BASE trade-offs."
            ),
            parent_topic_id=_P1,
        ),
        dict(
            id=_T4,
            name="Frontend Development",
            description=(
                "Browser fundamentals, React / component architecture, "
                "state management, performance optimisation, and accessibility."
            ),
            parent_topic_id=_P1,
        ),
        dict(
            id=_T5,
            name="Backend Development",
            description=(
                "Server architecture, REST / GraphQL API design, "
                "async programming, middleware patterns, and service reliability."
            ),
            parent_topic_id=_P1,
        ),
        dict(
            id=_T6,
            name="DevOps & Cloud",
            description=(
                "CI/CD pipelines, containerisation (Docker/Kubernetes), "
                "infrastructure as code, observability, and cloud provider services."
            ),
            parent_topic_id=_P1,
        ),
        dict(
            id=_T7,
            name="Machine Learning & AI",
            description=(
                "ML fundamentals, model evaluation, feature engineering, "
                "neural networks, LLM fine-tuning, and productionising AI systems."
            ),
            parent_topic_id=_P1,
        ),
        # ── Behavioral Skills children ────────────────────────────────────────
        dict(
            id=_B1,
            name="Leadership & Teamwork",
            description=(
                "Demonstrating ownership, cross-functional collaboration, "
                "conflict resolution, and mentoring using the STAR method."
            ),
            parent_topic_id=_P2,
        ),
        dict(
            id=_B2,
            name="Problem Solving & Decision Making",
            description=(
                "Frameworks for breaking down ambiguous problems, "
                "trade-off analysis, prioritisation under pressure, and bias for action."
            ),
            parent_topic_id=_P2,
        ),
        dict(
            id=_B3,
            name="Communication & Presentation",
            description=(
                "Structuring clear answers, tailoring messaging to the audience, "
                "handling pushback, and delivering concise executive-level updates."
            ),
            parent_topic_id=_P2,
        ),
        # ── Domain Expertise children ─────────────────────────────────────────
        dict(
            id=_D1,
            name="API Design & Architecture",
            description=(
                "RESTful conventions, versioning strategies, OpenAPI specs, "
                "rate limiting, pagination, and designing resilient API contracts."
            ),
            parent_topic_id=_P3,
        ),
        dict(
            id=_D2,
            name="Security & Authentication",
            description=(
                "OAuth 2.0 / OIDC flows, JWT, CSRF / XSS / SQL-injection "
                "prevention, HTTPS, secret management, and zero-trust principles."
            ),
            parent_topic_id=_P3,
        ),
        dict(
            id=_D3,
            name="Mobile Development",
            description=(
                "iOS / Android architecture patterns, React Native vs native, "
                "offline-first design, push notifications, and App Store constraints."
            ),
            parent_topic_id=_P3,
        ),
    ])


def downgrade() -> None:
    conn = op.get_bind()
    ids = [
        _P1, _P2, _P3,
        _T1, _T2, _T3, _T4, _T5, _T6, _T7,
        _B1, _B2, _B3,
        _D1, _D2, _D3,
    ]
    conn.execute(
        sa.text("DELETE FROM topics WHERE id = ANY(:ids)"),
        {"ids": ids},
    )


# ── Helpers ────────────────────────────────────────────────────────────────────


def _insert_topics(rows: list[dict]) -> None:
    """Bulk-insert topic rows; skips any that already exist (idempotent)."""
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO topics (id, name, description, is_global, parent_topic_id,
                                created_at, updated_at)
            VALUES (:id, :name, :description, TRUE, :parent_topic_id,
                    now(), now())
            ON CONFLICT (id) DO NOTHING
        """),
        rows,
    )
