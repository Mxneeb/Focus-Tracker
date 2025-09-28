"""State Classification module for GameBuddy Focus Tracker.
Determines the user's overall state based on calculated metrics.
"""

class StateModule:
    """Classifies the user's state based on input metrics."""
    def __init__(self, config=None):
        """Initialize the state module.
        Args:
            config (AppConfig, optional): Application configuration. Defaults to None.
        """
        self.config = config # Config might hold thresholds in the future
        # Define state thresholds (these could be loaded from config)
        self.thresholds = {
            "attention_high": 85,
            "attention_focused": 70,
            "attention_low": 50,
            "engagement_high": 70,
            "engagement_moderate": 50,
            "frustration_critical": 70,
            "frustration_high": 40,
            "fatigue_critical": 70,
            "fatigue_high": 40,
            "distraction_critical": 60,
            "distraction_high": 30,
            "distraction_low_for_focus": 15,
            "frustration_low_for_focus": 25,
            "fatigue_low_for_focus": 25
        }
        print("State Module initialized.")

    def classify_state(self, metrics):
        """Classifies the user's state based on the provided metrics.

        Args:
            metrics (dict): A dictionary of calculated metrics (attention, fatigue, etc.).

        Returns:
            str: The classified user state (e.g., "Highly Focused & Engaged", "Highly Frustrated").
        """
        if not metrics:
            return "Unknown"

        att = metrics.get("attention", 0)
        eng = metrics.get("engagement", 0)
        fru = metrics.get("frustration", 0)
        fat = metrics.get("fatigue", 0)
        dis = metrics.get("distraction", 0)

        # Priority: Critical states first
        if fat >= self.thresholds["fatigue_critical"]:
            return "Highly Fatigued"
        if fru >= self.thresholds["frustration_critical"]:
            return "Highly Frustrated"
        if dis >= self.thresholds["distraction_critical"] and att < self.thresholds["attention_low"]:
            return "Highly Distracted"

        # High states
        if fat >= self.thresholds["fatigue_high"]:
            return "Slightly Fatigued" # As per spec, "Feeling tired?" message
        if fru >= self.thresholds["frustration_high"]:
            return "Slightly Frustrated" # As per spec, "Feeling a bit tense?" message
        if dis >= self.thresholds["distraction_high"] and att < self.thresholds["attention_focused"]:
            return "Slightly Distracted"

        # Positive states
        if att >= self.thresholds["attention_high"] and \
           eng >= self.thresholds["engagement_high"] and \
           fru < self.thresholds["frustration_low_for_focus"] and \
           fat < self.thresholds["fatigue_low_for_focus"] and \
           dis < self.thresholds["distraction_low_for_focus"]:
            return "Highly Focused & Engaged"
        
        if att >= self.thresholds["attention_focused"] and \
           eng >= self.thresholds["engagement_moderate"] and \
           fru < self.thresholds["frustration_high"] and \
           fat < self.thresholds["fatigue_high"] and \
           dis < self.thresholds["distraction_high"]:
            return "Focused"

        # Default/Neutral state
        return "Neutral/Calm"

if __name__ == "__main__":
    print("Testing State Module...")
    state_mod = StateModule()

    test_metrics_1 = {"attention": 90, "engagement": 80, "frustration": 10, "fatigue": 10, "distraction": 5}
    print(f"Metrics: {test_metrics_1} -> State: {state_mod.classify_state(test_metrics_1)}") # Expected: Highly Focused & Engaged

    test_metrics_2 = {"attention": 60, "engagement": 40, "frustration": 80, "fatigue": 20, "distraction": 30}
    print(f"Metrics: {test_metrics_2} -> State: {state_mod.classify_state(test_metrics_2)}") # Expected: Highly Frustrated

    test_metrics_3 = {"attention": 40, "engagement": 30, "frustration": 20, "fatigue": 80, "distraction": 70}
    print(f"Metrics: {test_metrics_3} -> State: {state_mod.classify_state(test_metrics_3)}") # Expected: Highly Fatigued
    
    test_metrics_4 = {"attention": 45, "engagement": 30, "frustration": 20, "fatigue": 20, "distraction": 65}
    print(f"Metrics: {test_metrics_4} -> State: {state_mod.classify_state(test_metrics_4)}") # Expected: Highly Distracted

    test_metrics_5 = {"attention": 75, "engagement": 60, "frustration": 30, "fatigue": 30, "distraction": 25}
    print(f"Metrics: {test_metrics_5} -> State: {state_mod.classify_state(test_metrics_5)}") # Expected: Focused

    test_metrics_6 = {"attention": 65, "engagement": 55, "frustration": 50, "fatigue": 30, "distraction": 25}
    print(f"Metrics: {test_metrics_6} -> State: {state_mod.classify_state(test_metrics_6)}") # Expected: Slightly Frustrated

    test_metrics_7 = {"attention": 65, "engagement": 55, "frustration": 30, "fatigue": 50, "distraction": 25}
    print(f"Metrics: {test_metrics_7} -> State: {state_mod.classify_state(test_metrics_7)}") # Expected: Slightly Fatigued

    test_metrics_8 = {"attention": 60, "engagement": 50, "frustration": 20, "fatigue": 20, "distraction": 35}
    print(f"Metrics: {test_metrics_8} -> State: {state_mod.classify_state(test_metrics_8)}") # Expected: Slightly Distracted
    
    test_metrics_9 = {"attention": 60, "engagement": 40, "frustration": 20, "fatigue": 20, "distraction": 20}
    print(f"Metrics: {test_metrics_9} -> State: {state_mod.classify_state(test_metrics_9)}") # Expected: Neutral/Calm

    print("State Module test complete.")

