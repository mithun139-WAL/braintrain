import re
import logging
from typing import Dict, Any, List, Optional
from app.ai.orchestrators.contracts.interview_contracts import InterviewPhase

logger = logging.getLogger("communication_engine")

FILLER_WORDS = [
    "um", "uh", "ah", "er", "like", "you know", "sort of", "kind of",
    "actually", "basically", "literally", "honestly", "well", "so",
    "i mean", "right", "okay", "you see", "anyway"
]

HEDGING_PHRASES = [
    "i think", "maybe", "probably", "possibly", "i believe", "sort of",
    "kind of", "not sure", "i guess", "i suppose", "perhaps", "might"
]

EXECUTIVE_PRESENCE_MARKERS = [
    "there are three", "firstly", "secondly", "finally", "specifically",
    "the core tradeoff", "in conclusion", "our primary goal", "key metrics",
    "business impact", "we chose to", "i decided"
]

TRANSITION_WORDS = [
    "however", "therefore", "consequently", "furthermore", "additionally",
    "in contrast", "specifically", "as a result", "subsequently", "first",
    "next", "then"
]

class CommunicationIntelligenceEngine:
    """
    CommunicationIntelligenceEngine analyzes candidate verbal responses.
    Evaluates structure (STAR/PREP), detects rambling/verbosity, sentence fragmentation,
    hedging language, transition quality, answer framing, and executive presence.
    """

    def __init__(self):
        pass

    def analyze_response_structure(self, text: str, phase: InterviewPhase) -> Dict[str, Any]:
        """
        Analyze structural alignment. Detects STAR, PREP, or Executive summaries.
        """
        text_lower = text.lower()
        star_components = {
            "situation": [r"\bsituation\b", r"\bcontext\b", r"\bscenario\b", r"\bwas working\b", r"\bteam\b"],
            "task": [r"\btask\b", r"\bgoal\b", r"\bobjective\b", r"\bneeded to\b", r"\bhad to\b"],
            "action": [r"\bi did\b", r"\bi built\b", r"\bi designed\b", r"\bi implemented\b", r"\bmy role\b", r"\bwe decided\b"],
            "result": [r"\bresult\b", r"\boutcome\b", r"\bimpact\b", r"\bmetric\b", r"\bachieved\b", r"\blead to\b"]
        }

        prep_components = {
            "point": [r"\bpoint\b", r"\bmain idea\b", r"\bprimary reason\b", r"\bi assert\b"],
            "reason": [r"\breason\b", r"\bbecause\b", r"\bdue to\b", r"\bsince\b"],
            "example": [r"\bexample\b", r"\binstance\b", r"\bfor example\b", r"\bsuch as\b"],
            "point_recap": [r"\bconclude\b", r"\btherefore\b", r"\bthat is why\b", r"\bin short\b"]
        }

        # Count detected STAR components
        star_detected = []
        for comp, patterns in star_components.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                star_detected.append(comp)

        # Count detected PREP components
        prep_detected = []
        for comp, patterns in prep_components.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                prep_detected.append(comp)

        star_score = (len(star_detected) / 4.0) * 100
        prep_score = (len(prep_detected) / 4.0) * 100

        # Choose the structure with highest matched components
        if star_score >= prep_score and star_score > 0:
            structure_type = "STAR"
            score = star_score
            components = star_detected
        elif prep_score > 0:
            structure_type = "PREP"
            score = prep_score
            components = prep_detected
        else:
            structure_type = "NONE"
            score = 0.0
            components = []

        # Executive summary detection (has clear initial summary + conclusion)
        has_exec_summary = len(text.split()) > 40 and any(re.search(p, text_lower) for p in EXECUTIVE_PRESENCE_MARKERS)
        if has_exec_summary and structure_type == "NONE":
            structure_type = "EXECUTIVE_SUMMARY"
            score = 75.0
            components = ["summary_framing"]

        return {
            "structure_type": structure_type,
            "structure_score": round(score, 1),
            "components_detected": components,
            "has_structured_response": score >= 50.0 or has_exec_summary
        }

    def detect_rambling(self, text: str, response_duration_seconds: float = 0.0) -> Dict[str, Any]:
        """
        Detect rambling based on word count, unique words ratio, and repetitive phrases.
        """
        words = text.split()
        word_count = len(words)
        if word_count == 0:
            return {"rambling_score": 0.0, "is_rambling": False, "reason": "No speech"}

        unique_words = set(w.lower() for w in words)
        unique_ratio = len(unique_words) / word_count

        # Count repetitions of phrases
        repetitive_score = 0.0
        phrases = [text[i:i+15].lower() for i in range(0, len(text)-15, 5)]
        if len(phrases) > 10:
            repetitions = len(phrases) - len(set(phrases))
            repetitive_score = (repetitions / len(phrases)) * 100.0

        # Rambling factors: high word count, low vocabulary diversity, repetitive phrases
        # If response is over 200 words, starting to risk rambling
        length_penalty = max(0.0, (word_count - 180) * 0.3)
        diversity_penalty = max(0.0, (0.6 - unique_ratio) * 100)
        repetition_penalty = min(30.0, repetitive_score * 0.5)

        rambling_score = min(100.0, length_penalty + diversity_penalty + repetition_penalty)
        is_rambling = rambling_score > 60.0

        reasons = []
        if length_penalty > 10:
            reasons.append("High word count for a single answer")
        if diversity_penalty > 15:
            reasons.append("Low vocabulary diversity (repetitive phrasing)")
        if repetition_penalty > 10:
            reasons.append("Frequent phrase repetition patterns detected")

        return {
            "rambling_score": round(rambling_score, 1),
            "is_rambling": is_rambling,
            "reasons": reasons,
            "word_count": word_count
        }

    def detect_fragmentation(self, text: str) -> Dict[str, Any]:
        """
        Detect sentence fragmentation, abrupt thought switching, or incomplete phrasing.
        """
        # Count break symbols (ellipses, trailing dashes, incomplete clauses)
        fragment_markers = len(re.findall(r'(\.\.\.|---| - | -|- )', text))
        
        # Sentences with fewer than 4 words (excluding brief agreements)
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 0]
        very_short_sentences = sum(1 for s in sentences if len(s.split()) < 4)
        
        word_count = len(text.split())
        if word_count == 0:
            return {"fragmentation_score": 0.0}

        score = (fragment_markers * 15.0) + (very_short_sentences * 10.0)
        score = min(100.0, score)

        return {
            "fragmentation_score": round(score, 1),
            "is_fragmented": score > 50.0,
            "evidence": f"Detected {fragment_markers} fragment markers and {very_short_sentences} short sentences."
        }

    def detect_uncertainty_language(self, text: str) -> Dict[str, Any]:
        """
        Track filler words and hedging phrases indicating low confidence.
        """
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        if word_count == 0:
            return {"uncertainty_score": 0.0, "filler_count": 0, "hedge_count": 0}

        filler_count = sum(len(re.findall(r'\b' + re.escape(fw) + r'\b', text_lower)) for fw in FILLER_WORDS)
        hedge_count = sum(len(re.findall(r'\b' + re.escape(hp) + r'\b', text_lower)) for hp in HEDGING_PHRASES)

        filler_rate = (filler_count / word_count) * 100
        hedge_rate = (hedge_count / word_count) * 100

        # Score increases with frequency of uncertainty markers
        score = (filler_rate * 4.0) + (hedge_rate * 6.0)
        score = min(100.0, score)

        return {
            "uncertainty_score": round(score, 1),
            "filler_count": filler_count,
            "hedge_count": hedge_count,
            "filler_rate_percent": round(filler_rate, 2),
            "hedge_rate_percent": round(hedge_rate, 2)
        }

    def detect_executive_presence(self, text: str) -> Dict[str, Any]:
        """
        Measures assertive, decision-oriented, and structured executive language.
        Executive presence is strong when hedging is low, structure is clear,
        and structured verbal anchors are used.
        """
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        if word_count == 0:
            return {"executive_presence_score": 0.0}

        # Count assertive markers
        presence_matches = sum(1 for m in EXECUTIVE_PRESENCE_MARKERS if m in text_lower)
        
        # Calculate ratio
        uncert = self.detect_uncertainty_language(text)
        uncertainty_penalty = uncert["uncertainty_score"] * 0.5
        
        # Base score starts at 50, gets bonuses for presence markers and penalties for uncertainty
        base_presence = 50.0 + (presence_matches * 12.0)
        score = base_presence - uncertainty_penalty
        score = min(100.0, max(0.0, score))

        return {
            "executive_presence_score": round(score, 1),
            "markers_detected": presence_matches,
            "is_executive_presence_strong": score >= 70.0
        }

    def analyze_narrative_flow(self, text: str) -> Dict[str, Any]:
        """
        Analyze narrative flow, transition word quality, and overall coherence.
        """
        text_lower = text.lower()
        
        # Analyze transition count
        transition_matches = sum(1 for tw in TRANSITION_WORDS if re.search(r'\b' + re.escape(tw) + r'\b', text_lower))
        
        # Analyze sentence counts
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 0]
        sentence_count = len(sentences)
        
        if sentence_count == 0:
            return {"narrative_flow_score": 0.0}

        transition_density = transition_matches / sentence_count
        
        # Perfect density is around 0.5 to 1.0 transitions per sentence
        if transition_density >= 0.5:
            transition_score = 100.0
        else:
            transition_score = (transition_density / 0.5) * 100.0

        # Penalize if narrative has abrupt structural jumps (low sentence diversity)
        flow_score = transition_score * 0.6 + min(100, sentence_count * 10) * 0.4

        return {
            "narrative_flow_score": round(flow_score, 1),
            "transition_count": transition_matches,
            "transition_density": round(transition_density, 2)
        }

    def analyze_transition_quality(self, text: str) -> float:
        """Helper to return transition quality score directly."""
        flow = self.analyze_narrative_flow(text)
        return flow["narrative_flow_score"]

    def analyze_answer_framing(self, text: str) -> float:
        """
        Evaluates the opening and closing of the response.
        Should have a clear thesis/introduction and a summarizing wrap-up statement.
        """
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 0]
        if len(sentences) < 2:
            return 30.0  # Fails framing structure

        opening = sentences[0].lower()
        closing = sentences[-1].lower()

        opening_score = 0.0
        closing_score = 0.0

        # Good openings outline the topic
        opening_anchors = ["i will", "want to address", "three key", "to explain", "regarding", "first", "in my experience"]
        if any(anchor in opening for anchor in opening_anchors):
            opening_score = 50.0

        # Good closings summarize or show result
        closing_anchors = ["therefore", "that is how", "in conclusion", "resulted in", "which led to", "overall", "lessons learned"]
        if any(anchor in closing for anchor in closing_anchors):
            closing_score = 50.0

        return opening_score + closing_score
