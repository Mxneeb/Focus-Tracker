"""Adaptive Coaching Module for GameBuddy Focus Tracker.
Learns user patterns and adapts feedback over time.
"""

import time
import json

class AdaptiveCoachingModule:
    """Handles adaptive coaching logic."""
    def __init__(self, config=None, storage_manager=None):
        """Initialize the adaptive coaching module.
        Args:
            config (AppConfig, optional): Application configuration.
            storage_manager (StorageManager, optional): For loading/saving patterns.
        """
        self.config = config
        self.storage_manager = storage_manager
        self.user_patterns = {
            "frustration_triggers": [], # e.g., [{"timestamp": ts, "metrics_before": {}, "game_event": "unknown"}]
            "fatigue_onset_times": [] # e.g., [{"timestamp": ts, "session_duration_minutes": 60}]
        }
        self.min_data_points_for_adaptation = self.config.get_setting("adaptive_coaching.min_data_points", 10) if self.config else 10
        self.load_patterns()
        print("Adaptive Coaching Module initialized.")

    def load_patterns(self):
        """Loads user patterns from storage."""
        if self.storage_manager:
            patterns = self.storage_manager.load_adaptive_patterns()
            if patterns:
                self.user_patterns = patterns
                print("Loaded adaptive coaching patterns.")
            else:
                print("No existing adaptive coaching patterns found or error loading.")
        else:
            print("Storage manager not available, cannot load adaptive patterns.")

    def save_patterns(self):
        """Saves current user patterns to storage."""
        if self.storage_manager:
            self.storage_manager.save_adaptive_patterns(self.user_patterns)
            print("Saved adaptive coaching patterns.")
        else:
            print("Storage manager not available, cannot save adaptive patterns.")

    def update(self, current_state, metrics):
        """Updates user patterns based on current state and metrics.
        This is a placeholder for more sophisticated pattern learning.
        """
        if not self.config or not self.config.get_setting("adaptive_coaching_enabled", True):
            return

        timestamp = time.time()
        if current_state == "Highly Frustrated":
            # Log potential frustration trigger
            # In a real app, we might try to get context (e.g., game event if integrated)
            self.user_patterns["frustration_triggers"].append({
                "timestamp": timestamp,
                "metrics_at_trigger": metrics,
                # "game_context": get_current_game_context() # Hypothetical
            })
            # Keep a limited history
            if len(self.user_patterns["frustration_triggers"]) > 50:
                self.user_patterns["frustration_triggers"].pop(0)
            self.save_patterns() # Save periodically or on significant change

        if current_state == "Highly Fatigued":
            # Log fatigue onset
            # This would ideally use session start time to calculate duration
            self.user_patterns["fatigue_onset_times"].append({
                "timestamp": timestamp,
                "metrics_at_onset": metrics,
                # "session_duration_minutes": calculate_session_duration() # Hypothetical
            })
            if len(self.user_patterns["fatigue_onset_times"]) > 50:
                self.user_patterns["fatigue_onset_times"].pop(0)
            self.save_patterns()

    def adapt_message(self, original_message, current_state):
        """Adapts the feedback message based on learned patterns.
        Placeholder logic.
        """
        if not self.config or not self.config.get_setting("adaptive_coaching_enabled", True):
            return original_message

        adapted_message = original_message

        if current_state == "Slightly Frustrated" or current_state == "Highly Frustrated":
            if len(self.user_patterns["frustration_triggers"]) >= self.min_data_points_for_adaptation:
                # Example: If frustration often occurs around a certain time of day or after X hours of play
                # This is highly simplified.
                num_triggers = len(self.user_patterns["frustration_triggers"])
                # adapted_message += f" (Note: We've seen {num_triggers} frustration spikes recently.)"
                # A more useful adaptation would be to suggest a specific strategy that worked before,
                # or remind about a common trigger if identified.
                pass # Add more sophisticated logic here

        if current_state == "Slightly Fatigued" or current_state == "Highly Fatigued":
            if len(self.user_patterns["fatigue_onset_times"]) >= self.min_data_points_for_adaptation:
                # Example: If fatigue usually sets in after X minutes
                # adapted_message += " (Remember, breaks around this time often help you!)"
                pass # Add more sophisticated logic here
        
        return adapted_message

if __name__ == "__main__":
    print("Testing Adaptive Coaching Module...")

    # Mock config and storage for testing
    class DummyConfig:
        def get_setting(self, key, default=None):
            if key == "adaptive_coaching.min_data_points": return 3
            if key == "adaptive_coaching_enabled": return True
            return default

    class DummyStorageManager:
        def __init__(self):
            self.patterns = None
        def load_adaptive_patterns(self):
            print("(DummyStorage) Loading patterns...")
            return self.patterns
        def save_adaptive_patterns(self, patterns_data):
            print(f"(DummyStorage) Saving patterns: {json.dumps(patterns_data)[:100]}...")
            self.patterns = patterns_data

    config = DummyConfig()
    storage = DummyStorageManager()
    coach = AdaptiveCoachingModule(config=config, storage_manager=storage)

    # Simulate some events
    metrics_frustrated = {"attention": 30, "frustration": 80, "fatigue": 20}
    metrics_fatigued = {"attention": 40, "frustration": 20, "fatigue": 75}

    coach.update("Highly Frustrated", metrics_frustrated)
    time.sleep(0.1)
    coach.update("Highly Fatigued", metrics_fatigued)
    time.sleep(0.1)
    coach.update("Highly Frustrated", metrics_frustrated)
    time.sleep(0.1)
    coach.update("Highly Frustrated", metrics_frustrated) # Now meets min_data_points for frustration

    original_msg_frust = "Feeling frustrated?"
    adapted_msg_frust = coach.adapt_message(original_msg_frust, "Slightly Frustrated")
    print(f"Original Frustration Msg: {original_msg_frust}")
    print(f"Adapted Frustration Msg: {adapted_msg_frust}")

    original_msg_fatigue = "Feeling tired?"
    adapted_msg_fatigue = coach.adapt_message(original_msg_fatigue, "Slightly Fatigued")
    print(f"Original Fatigue Msg: {original_msg_fatigue}")
    print(f"Adapted Fatigue Msg: {adapted_msg_fatigue}")
    
    # Test loading previously "saved" patterns
    print("\nRe-initializing coach to test loading patterns...")
    coach2 = AdaptiveCoachingModule(config=config, storage_manager=storage)
    adapted_msg_frust2 = coach2.adapt_message(original_msg_frust, "Slightly Frustrated")
    print(f"Adapted Frustration Msg (coach2): {adapted_msg_frust2}")
    assert len(coach2.user_patterns["frustration_triggers"]) == 3

    print("\nAdaptive Coaching Module test complete.")

