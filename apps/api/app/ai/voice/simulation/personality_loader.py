import os
import json
import logging
from typing import Dict, Any, Optional
from app.ai.voice.simulation.personality_profiles import PersonalityProfile

logger = logging.getLogger("personality_loader")

class PersonalityLoader:
    @staticmethod
    def load_from_file(filepath: str) -> Optional[PersonalityProfile]:
        """
        Loads an interviewer personality profile from a YAML or JSON file.
        """
        if not os.path.exists(filepath):
            logger.error("Personality profile file not found: %s", filepath)
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if filepath.endswith(".json"):
                data = json.loads(content)
            else:
                # Self-contained light YAML line parser
                data = PersonalityLoader._parse_simple_yaml(content)
            
            return PersonalityLoader.load_from_dict(data)
        except Exception as e:
            logger.exception("Failed to load personality file %s: %s", filepath, e)
            return None

    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> PersonalityProfile:
        char = data.get("characteristics", {})
        return PersonalityProfile(
            name=data.get("name", "Default Interviewer"),
            archetype=data.get("archetype", "Standard"),
            pacing_speed=float(char.get("pacing_speed", 1.0)),
            interruption_frequency=float(char.get("interruption_frequency", 0.5)),
            silence_tolerance=float(char.get("silence_tolerance", 1.0)),
            skepticism_level=float(char.get("skepticism_level", 0.5)),
            technical_depth=float(char.get("technical_depth", 0.5)),
            followup_aggressiveness=float(char.get("followup_aggressiveness", 0.5)),
            verbosity_tolerance=float(char.get("verbosity_tolerance", 0.5)),
            ambiguity_tolerance=float(char.get("ambiguity_tolerance", 0.5)),
            pressure_intensity=float(char.get("pressure_intensity", 0.5)),
            conversational_warmth=float(char.get("conversational_warmth", 0.5)),
            challenge_escalation=data.get("challenge_escalation", "Standard"),
            acknowledgment_patterns=data.get("acknowledgment_patterns", []),
            custom_prompts=data.get("custom_prompts", {})
        )

    @staticmethod
    def _parse_simple_yaml(yaml_content: str) -> Dict[str, Any]:
        """
        A minimalist YAML parser that parses basic key-value, lists, and nested single-level maps.
        """
        result: Dict[str, Any] = {}
        current_section = None
        current_list_key = None

        for line in yaml_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if this is a list item
            if line.startswith("-"):
                val = line[1:].strip().strip('"').strip("'")
                if current_list_key and isinstance(result.get(current_list_key), list):
                    result[current_list_key].append(val)
                elif current_section and current_list_key and isinstance(result[current_section].get(current_list_key), list):
                    result[current_section][current_list_key].append(val)
                continue

            # Section headers or single key-values
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")

                # Nested map starts (e.g. characteristics:)
                if not val:
                    # If indentation isn't checked, we just check section names
                    if key in ["characteristics", "custom_prompts"]:
                        current_section = key
                        result[key] = {}
                    else:
                        current_list_key = key
                        result[key] = []
                    continue

                # Normal key-value parsing
                # Convert values to float/int if possible
                parsed_val = val
                if val.lower() == "true":
                    parsed_val = True
                elif val.lower() == "false":
                    parsed_val = False
                else:
                    try:
                        parsed_val = float(val) if "." in val else int(val)
                    except ValueError:
                        pass

                if current_section:
                    # Check if line is indented, if not reset current_section
                    # For simplicity, we just add it to result[section]
                    result[current_section][key] = parsed_val
                else:
                    result[key] = parsed_val
        
        return result
