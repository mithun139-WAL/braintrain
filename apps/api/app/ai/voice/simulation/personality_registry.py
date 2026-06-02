import os
import logging
from typing import Dict, Optional

from app.ai.voice.simulation.personality_profiles import PersonalityProfile
from app.ai.voice.simulation.personality_loader import PersonalityLoader
from app.db.models.agent_persona import AgentPersona
from app.db.session import SessionLocal

logger = logging.getLogger("personality_registry")


class PersonalityRegistry:
    def __init__(self, personas_dir: str = "personas"):
        self.personas_dir = personas_dir
        self.profiles: Dict[str, PersonalityProfile] = {}
        self._load_default_profiles()

    async def get_profile(self, name: str) -> PersonalityProfile:
        """
        Retrieves a loaded profile by key. Checks database first, then falls back to local cache/files.
        """
        # Clean name format
        key = name.lower().replace(" ", "_")

        # Try database first so dashboard edits reflect instantly
        profile = await self._try_load_from_db(key)
        if profile:
            self.profiles[key] = profile
            return profile

        if key in self.profiles:
            return self.profiles[key]

        # Try loading dynamically from directory
        profile = self._try_load_dynamic(key)
        if profile:
            self.profiles[key] = profile
            return profile

        # Fallback profile
        logger.warning("Profile '%s' not found in registry. Using standard fallback.", name)
        return self.profiles["standard_interviewer"]

    def register_profile(self, key: str, profile: PersonalityProfile) -> None:
        self.profiles[key.lower()] = profile

    def _load_default_profiles(self) -> None:
        """Loads static baseline profiles."""
        standard = PersonalityProfile(
            name="Standard Interviewer",
            archetype="Professional Coach",
            pacing_speed=1.0,
            interruption_frequency=0.4,
            silence_tolerance=1.0,
            skepticism_level=0.5,
            technical_depth=0.5,
            followup_aggressiveness=0.5,
            verbosity_tolerance=0.5,
            ambiguity_tolerance=0.5,
            pressure_intensity=0.5,
            conversational_warmth=0.6,
            acknowledgment_patterns=["Got it.", "Makes sense.", "Okay."]
        )
        self.profiles["standard_interviewer"] = standard

    async def _try_load_from_db(self, key: str) -> Optional[PersonalityProfile]:
        from sqlalchemy import select

        try:
            async with SessionLocal() as session:
                stmt = select(AgentPersona)
                result = await session.execute(stmt)
                personas = result.scalars().all()
                for p in personas:
                    if p.name.lower().replace(" ", "_") == key:
                        return PersonalityProfile(
                            name=p.name,
                            archetype=p.archetype,
                            pacing_speed=p.pacing_speed,
                            interruption_frequency=p.interruption_frequency,
                            silence_tolerance=p.silence_tolerance,
                            skepticism_level=p.skepticism_level,
                            technical_depth=p.technical_depth,
                            followup_aggressiveness=p.followup_aggressiveness,
                            verbosity_tolerance=p.verbosity_tolerance,
                            ambiguity_tolerance=p.ambiguity_tolerance,
                            pressure_intensity=p.pressure_intensity,
                            conversational_warmth=p.conversational_warmth,
                            challenge_escalation=p.challenge_escalation,
                            acknowledgment_patterns=p.acknowledgment_patterns or [],
                            custom_prompts=p.custom_prompts or {},
                        )
        except Exception as exc:
            logger.error("Error loading persona '%s' from database: %s", key, exc)
        return None

    def _try_load_dynamic(self, key: str) -> Optional[PersonalityProfile]:
        # Walk directories in search of key.yaml or key.json
        if not os.path.exists(self.personas_dir):
            return None

        for root, _, files in os.walk(self.personas_dir):
            for file in files:
                fname, ext = os.path.splitext(file)
                if fname.lower() == key and ext in [".yaml", ".yml", ".json"]:
                    filepath = os.path.join(root, file)
                    return PersonalityLoader.load_from_file(filepath)
        return None

    async def seed_db_from_files(self) -> None:
        """Seeds the DB table agent_personas from static files if it is empty."""
        from sqlalchemy import select, func

        try:
            async with SessionLocal() as session:
                stmt = select(func.count()).select_from(AgentPersona)
                res = await session.execute(stmt)
                count = res.scalar()
                if count > 0:
                    return

                if not os.path.exists(self.personas_dir):
                    return

                logger.info("Database agent_personas table is empty. Seeding from files in '%s'...", self.personas_dir)
                for root, _, files in os.walk(self.personas_dir):
                    for file in files:
                        fname, ext = os.path.splitext(file)
                        if ext in [".yaml", ".yml", ".json"]:
                            filepath = os.path.join(root, file)
                            try:
                                profile = PersonalityLoader.load_from_file(filepath)
                                if profile:
                                    db_p = AgentPersona(
                                        name=profile.name,
                                        archetype=profile.archetype,
                                        pacing_speed=profile.pacing_speed,
                                        interruption_frequency=profile.interruption_frequency,
                                        silence_tolerance=profile.silence_tolerance,
                                        skepticism_level=profile.skepticism_level,
                                        technical_depth=profile.technical_depth,
                                        followup_aggressiveness=profile.followup_aggressiveness,
                                        verbosity_tolerance=profile.verbosity_tolerance,
                                        ambiguity_tolerance=profile.ambiguity_tolerance,
                                        pressure_intensity=profile.pressure_intensity,
                                        conversational_warmth=profile.conversational_warmth,
                                        challenge_escalation=profile.challenge_escalation,
                                        acknowledgment_patterns=profile.acknowledgment_patterns or [],
                                        custom_prompts=profile.custom_prompts or {},
                                    )
                                    session.add(db_p)
                            except Exception as ex:
                                logger.error("Failed to parse/seed persona file '%s': %s", filepath, ex)
                await session.commit()
                logger.info("Successfully seeded database with interviewer personas.")
        except Exception as exc:
            logger.error("Failed to seed database from files: %s", exc)


