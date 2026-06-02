import uuid
import math
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.learning_memory import LearningMemoryNode, LearningMemoryEdge

logger = logging.getLogger("memory_reinforcement_engine")

class MemoryReinforcementEngine:
    """
    Memory Reinforcement Engine for training stress-resistant recall.
    Calculates retention strength, schedules reviews (1-day, 3-day, 7-day intervals),
    and flags concept fragility (e.g., concepts the candidate memorized but fails under pressure).
    """

    def __init__(self):
        pass

    def calculate_retention_score(self, node: LearningMemoryNode) -> float:
        """
        Calculate current retention strength using an exponential decay model.
        R = 100 * e^(-t / S)
        Where t is elapsed time in days, and S is memory stability (in days).
        """
        last_exposed = node.last_exposed_at
        if hasattr(last_exposed, "tzinfo") and last_exposed.tzinfo is not None:
            last_exposed = last_exposed.replace(tzinfo=None)

        elapsed_days = (datetime.utcnow() - last_exposed).total_seconds() / 86400.0
        elapsed_days = max(0.0, elapsed_days)

        # Memory stability S depends on exposure count, mastery level, and retry success rate
        # S ranges from 1.0 day to 90.0 days
        base_stability = max(1.0, (node.mastery_level / 10.0))
        retry_factor = max(0.2, node.retry_success_rate)
        exposure_bonus = 1.0 + (0.4 * node.exposure_count)

        stability = base_stability * retry_factor * exposure_bonus
        stability = min(90.0, max(1.0, stability))

        retention = 100.0 * math.exp(-elapsed_days / stability)
        return round(min(100.0, max(0.0, retention)), 1)

    async def analyze_memory_strength(self, candidate_id: uuid.UUID, db: AsyncSession) -> List[LearningMemoryNode]:
        """
        Updates and returns the memory nodes for a candidate.
        Recalculates retention strength and updates classification flags.
        """
        stmt = select(LearningMemoryNode).where(LearningMemoryNode.candidate_id == candidate_id)
        result = await db.execute(stmt)
        nodes = list(result.scalars().all())

        for node in nodes:
            old_retention = node.retention_strength
            node.retention_strength = self.calculate_retention_score(node)

            # Update weak/strong classification thresholds
            node.is_weak_recall = node.retention_strength < 60.0
            node.is_strong_recall = node.retention_strength >= 80.0 and node.confidence_score >= 70.0

            # Volatility under pressure check
            node.is_fragile = (
                node.familiarity_score > 50.0 
                and node.pressure_recall_stability < 50.0
            )

            # Recalculate mastery level
            # Composite of familiarity, confidence, retention, and pressure stability
            node.mastery_level = round(
                node.familiarity_score * 0.2 +
                node.confidence_score * 0.2 +
                node.retention_strength * 0.3 +
                node.pressure_recall_stability * 0.3,
                1
            )

            logger.debug(
                f"Node {node.concept_name} updated: retention {old_retention} -> {node.retention_strength}, "
                f"mastery={node.mastery_level}"
            )

        await db.commit()
        return nodes

    async def detect_memory_decay(self, candidate_id: uuid.UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Detects nodes undergoing significant memory decay.
        Returns a list of nodes whose retention score has dropped below 70.0 since their last review.
        """
        nodes = await self.analyze_memory_strength(candidate_id, db)
        decaying_concepts = []

        for node in nodes:
            if node.retention_strength < 70.0:
                decaying_concepts.append({
                    "concept_name": node.concept_name,
                    "retention_strength": node.retention_strength,
                    "last_exposed_at": node.last_exposed_at.isoformat(),
                    "concept_type": node.concept_type
                })

        return decaying_concepts

    async def detect_recall_fragility(self, candidate_id: uuid.UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Detects concepts that are fragile under pressure.
        These are concepts where the candidate has high familiarity but low recall stability under stress.
        """
        nodes = await self.analyze_memory_strength(candidate_id, db)
        fragile_concepts = []

        for node in nodes:
            if node.is_fragile:
                fragile_concepts.append({
                    "concept_name": node.concept_name,
                    "familiarity_score": node.familiarity_score,
                    "pressure_recall_stability": node.pressure_recall_stability,
                    "mastery_level": node.mastery_level,
                    "reason": "High familiarity but fails under pressure"
                })

        return fragile_concepts

    async def schedule_reinforcement(
        self, 
        candidate_id: uuid.UUID, 
        concept_name: str, 
        interval_days: int, 
        db: AsyncSession
    ) -> Optional[LearningMemoryNode]:
        """
        Schedules a reinforcement session for a specific concept.
        Updates next_review_at and increments exposure count.
        """
        stmt = select(LearningMemoryNode).where(
            LearningMemoryNode.candidate_id == candidate_id,
            LearningMemoryNode.concept_name == concept_name
        )
        result = await db.execute(stmt)
        node = result.scalar_one_or_none()

        if not node:
            logger.warning(f"Failed to schedule reinforcement: concept '{concept_name}' not found for user {candidate_id}")
            return None

        node.next_review_at = datetime.utcnow() + timedelta(days=interval_days)
        node.exposure_count += 1
        node.last_exposed_at = datetime.utcnow()
        
        await db.commit()
        logger.info(f"Scheduled reinforcement for '{concept_name}' in {interval_days} days. Next review: {node.next_review_at}")
        return node

    async def generate_recall_drills(self, candidate_id: uuid.UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Generates active recall drills targeting weak or fragile concepts.
        """
        nodes = await self.analyze_memory_strength(candidate_id, db)
        drills = []

        # Target weak or fragile nodes first
        target_nodes = [n for n in nodes if n.is_weak_recall or n.is_fragile]
        
        # Sort by mastery ascending
        target_nodes.sort(key=lambda x: x.mastery_level)

        for node in target_nodes[:5]:  # Limit to top 5 urgent drills
            difficulty = "HIGH" if node.is_fragile else "MEDIUM"
            drills.append({
                "concept_name": node.concept_name,
                "concept_type": node.concept_type,
                "mastery_level": node.mastery_level,
                "retention_strength": node.retention_strength,
                "is_fragile": node.is_fragile,
                "drill_type": "PRESSURE_RECALL_CHALLENGE" if node.is_fragile else "CONCEPT_REINFORCEMENT",
                "recommended_difficulty": difficulty,
                "instruction": (
                    f"Explain '{node.concept_name}' and detail its tradeoffs under interruption."
                    if node.is_fragile else
                    f"Describe the core architecture of '{node.concept_name}' and provide a simple example."
                )
            })

        return drills

    async def generate_memory_recovery_exercises(self, candidate_id: uuid.UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Generates mental recovery exercises to help candidates rebuild recall pathways when blocked by stress.
        """
        # Get edges representing relationships (like prerequisite chains or recovery links)
        nodes = await self.analyze_memory_strength(candidate_id, db)
        weak_nodes = [n for n in nodes if n.is_weak_recall or n.is_fragile]
        
        recovery_exercises = []
        for node in weak_nodes[:3]:
            # Find related concepts that can serve as cognitive anchors
            stmt = select(LearningMemoryEdge).where(
                LearningMemoryEdge.candidate_id == candidate_id,
                (LearningMemoryEdge.source_node_id == node.id) | (LearningMemoryEdge.target_node_id == node.id)
            )
            edge_result = await db.execute(stmt)
            edges = edge_result.scalars().all()
            
            anchor_concepts = []
            for edge in edges:
                anchor_id = edge.target_node_id if edge.source_node_id == node.id else edge.source_node_id
                # Find concept name of anchor_id
                anchor_node = next((n for n in nodes if n.id == anchor_id), None)
                if anchor_node:
                    anchor_concepts.append(anchor_node.concept_name)

            recovery_exercises.append({
                "concept_name": node.concept_name,
                "anchors": anchor_concepts,
                "exercise": (
                    f"If you blank on '{node.concept_name}', bridge to it by first discussing "
                    f"'{', '.join(anchor_concepts)}' which are conceptually related."
                    if anchor_concepts else
                    f"If you blank on '{node.concept_name}', pause, state your requirements, "
                    f"and explain a basic version before building the full concept."
                )
            })
            
        return recovery_exercises
