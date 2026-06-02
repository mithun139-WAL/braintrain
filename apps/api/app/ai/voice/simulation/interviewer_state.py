class InterviewerState:
    def __init__(self, initial_warmth: float = 0.5, initial_skepticism: float = 0.5):
        self.patience_level: float = 1.0       # 0.0 (aggressive/hurrying) to 1.0 (patient)
        self.frustration_level: float = 0.0    # 0.0 (calm) to 1.0 (frustrated)
        self.skepticism_index: float = initial_skepticism
        self.active_warmth: float = initial_warmth
        
        # Tracking conversation flow metrics
        self.consecutive_turns_drilled: int = 0
        self.total_interruptions: int = 0
        self.consecutive_vague_answers: int = 0

    def reset_turn_counters(self) -> None:
        self.consecutive_turns_drilled = 0
        self.consecutive_vague_answers = 0

    def adjust_impressions(self, topic_drift: float, hesitation: float, verbosity: float) -> None:
        """
        Dynamically adjusts patience and frustration based on turn behavioral metrics.
        """
        # Verbose/Rambling answers reduce patience
        if verbosity > 70.0:
            self.patience_level = max(0.1, self.patience_level - 0.15)
            self.frustration_level = min(1.0, self.frustration_level + 0.1)
        
        # High topic drift (evasion) reduces patience rapidly and boosts skepticism
        if topic_drift > 60.0:
            self.consecutive_vague_answers += 1
            self.patience_level = max(0.0, self.patience_level - 0.25)
            self.skepticism_index = min(1.0, self.skepticism_index + 0.2)
        else:
            self.consecutive_vague_answers = max(0, self.consecutive_vague_answers - 1)

        # High hesitation slightly reduces pacing speed and bumps frustration if repeated
        if hesitation > 50.0:
            self.active_warmth = max(0.1, self.active_warmth - 0.05)
