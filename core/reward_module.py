"""Reward System Module for GameBuddy Focus Tracker.
Tracks achievements and provides positive reinforcement.
"""

import time
import json

class RewardModule:
    """Handles the reward system and achievements."""
    def __init__(self, config=None, storage_manager=None):
        """Initialize the reward module.
        Args:
            config (AppConfig, optional): Application configuration.
            storage_manager (StorageManager, optional): For loading/saving achievements.
        """
        self.config = config
        self.storage_manager = storage_manager
        self.achievements = {
            "focus_streak_10m": {"name": "Focused Mind (10 min)", "description": "Maintain high focus for 10 minutes straight.", "unlocked": False, "progress": 0, "target": 600, "type": "streak"}, # target in seconds
            "focus_streak_30m": {"name": "Laser Focus (30 min)", "description": "Maintain high focus for 30 minutes straight.", "unlocked": False, "progress": 0, "target": 1800, "type": "streak"},
            "frustration_managed_3x": {"name": "Cool Head (3 Times)", "description": "Successfully navigate 3 high frustration moments without quitting (placeholder logic).", "unlocked": False, "progress": 0, "target": 3, "type": "count"},
            "first_break_taken": {"name": "Smart Breaker", "description": "Took a suggested break when highly fatigued.", "unlocked": False, "progress": 0, "target": 1, "type": "event"}
        }
        self.last_focus_check_time = time.time()
        self.current_focus_streak_seconds = 0
        self.last_frustration_state = None
        self.load_achievements()
        print("Reward Module initialized.")

    def load_achievements(self):
        """Loads achievement progress from storage."""
        if self.storage_manager:
            stored_achievements = self.storage_manager.load_reward_data()
            if stored_achievements:
                for key, stored_data in stored_achievements.items():
                    if key in self.achievements:
                        self.achievements[key].update(stored_data)
                print("Loaded reward achievements data.")
            else:
                print("No existing reward achievements data found or error loading.")
        else:
            print("Storage manager not available, cannot load reward achievements.")

    def save_achievements(self):
        """Saves current achievement progress to storage."""
        if self.storage_manager:
            self.storage_manager.save_reward_data(self.achievements)
            print("Saved reward achievements data.")
        else:
            print("Storage manager not available, cannot save reward achievements.")

    def update(self, current_state, metrics):
        """Updates achievement progress based on current state and metrics."""
        if not self.config or not self.config.get_setting("reward_system_enabled", True):
            return

        current_time = time.time()
        time_delta = current_time - self.last_focus_check_time
        self.last_focus_check_time = current_time

        # --- Focus Streak Achievements ---
        is_highly_focused = (current_state == "Highly Focused & Engaged") or \
                            (metrics.get("attention", 0) > (self.config.get_setting("rewards.focus_streak_attention_threshold", 80) if self.config else 80) and \
                             metrics.get("distraction", 0) < (self.config.get_setting("rewards.focus_streak_distraction_threshold", 20) if self.config else 20))

        if is_highly_focused:
            self.current_focus_streak_seconds += time_delta
        else:
            self.current_focus_streak_seconds = 0 # Reset streak

        for ach_key in ["focus_streak_10m", "focus_streak_30m"]:
            achievement = self.achievements[ach_key]
            if not achievement["unlocked"]:
                achievement["progress"] = self.current_focus_streak_seconds
                if achievement["progress"] >= achievement["target"]:
                    achievement["unlocked"] = True
                    achievement["progress"] = achievement["target"] # Cap progress
                    print(f"Achievement Unlocked: {achievement['name']}!")
                    self.save_achievements()
        
        # --- Frustration Managed Achievement ---
        # This is a simplified placeholder. Real logic would need to detect a high frustration state
        # followed by a recovery to a calmer state without, for example, app closure.
        frustration_metric = metrics.get("frustration", 0)
        ach_fm3 = self.achievements["frustration_managed_3x"]
        if not ach_fm3["unlocked"]:
            if self.last_frustration_state and self.last_frustration_state >= 70 and frustration_metric < 40:
                # Assumes a transition from high frustration to low/managed
                ach_fm3["progress"] += 1
                print(f"Frustration managed event counted. Progress: {ach_fm3['progress']}/{ach_fm3['target']}")
                if ach_fm3["progress"] >= ach_fm3["target"]:
                    ach_fm3["unlocked"] = True
                    print(f"Achievement Unlocked: {ach_fm3['name']}!")
                self.save_achievements()
        self.last_frustration_state = frustration_metric

        # --- First Break Taken Achievement (Placeholder) ---
        # This would be triggered by an external event, e.g., user clicking a "Take Break" button
        # after being in "Highly Fatigued" state and receiving a suggestion.
        # For now, it remains a placeholder.

    def get_achievements(self):
        """Returns the current state of all achievements."""
        return self.achievements
    
    def get_unlocked_achievements_and_clear_notifications(self):
        """Returns a list of newly unlocked achievements and marks them as notified.
           This is a placeholder for a proper notification system.
        """
        newly_unlocked = []
        for key, ach in self.achievements.items():
            if ach["unlocked"] and not ach.get("notified", False):
                newly_unlocked.append(ach)
                ach["notified"] = True # Mark as notified
        if newly_unlocked:
            self.save_achievements() # Save notification status
        return newly_unlocked

if __name__ == "__main__":
    print("Testing Reward Module...")

    class DummyConfig:
        def get_setting(self, key, default=None):
            if key == "reward_system_enabled": return True
            if key == "rewards.focus_streak_attention_threshold": return 80
            if key == "rewards.focus_streak_distraction_threshold": return 20
            return default

    class DummyStorageManager:
        def __init__(self):
            self.rewards = None
        def load_reward_data(self):
            print("(DummyStorage) Loading reward data...")
            return self.rewards
        def save_reward_data(self, data):
            print(f"(DummyStorage) Saving reward data: {json.dumps(data)['focus_streak_10m']}...")
            self.rewards = data

    config = DummyConfig()
    storage = DummyStorageManager()
    reward_mod = RewardModule(config=config, storage_manager=storage)

    print("\nInitial Achievements:")
    for name, ach_data in reward_mod.get_achievements().items():
        print(f"- {ach_data['name']}: Unlocked - {ach_data['unlocked']}, Progress - {ach_data['progress']}/{ach_data['target']}")

    print("\nSimulating focus streak...")
    # Simulate 11 minutes of high focus
    mock_metrics_focused = {"attention": 85, "distraction": 10, "frustration": 10}
    start_time = time.time()
    reward_mod.last_focus_check_time = start_time
    for i in range(660): # 11 minutes * 60 seconds / ~0.5s loop time (approx)
        # time.sleep(0.01) # Simulate small time delta
        # In real app, time_delta is calculated based on actual loop time
        # For test, let's manually increment streak assuming 1s per call
        reward_mod.current_focus_streak_seconds = i + 1 
        reward_mod.update("Highly Focused & Engaged", mock_metrics_focused)
        if (i+1) % 60 == 0:
             print(f"  Streak at {reward_mod.current_focus_streak_seconds}s. 10m Unlocked: {reward_mod.achievements['focus_streak_10m']['unlocked']}")

    print("\nAchievements after focus streak simulation:")
    for name, ach_data in reward_mod.get_achievements().items():
        print(f"- {ach_data['name']}: Unlocked - {ach_data['unlocked']}, Progress - {ach_data['progress']}/{ach_data['target']}")
    assert reward_mod.achievements["focus_streak_10m"]["unlocked"] == True

    print("\nSimulating frustration management...")
    reward_mod.update("Neutral/Calm", {"frustration": 75}) # High frustration
    reward_mod.update("Neutral/Calm", {"frustration": 30}) # Recovered
    reward_mod.update("Neutral/Calm", {"frustration": 80}) # High
    reward_mod.update("Neutral/Calm", {"frustration": 20}) # Recovered
    reward_mod.update("Neutral/Calm", {"frustration": 70}) # High
    reward_mod.update("Neutral/Calm", {"frustration": 35}) # Recovered
    
    print("\nAchievements after frustration simulation:")
    for name, ach_data in reward_mod.get_achievements().items():
        print(f"- {ach_data['name']}: Unlocked - {ach_data['unlocked']}, Progress - {ach_data['progress']}/{ach_data['target']}")
    assert reward_mod.achievements["frustration_managed_3x"]["unlocked"] == True

    print("\nTesting newly unlocked notifications:")
    newly_unlocked = reward_mod.get_unlocked_achievements_and_clear_notifications()
    for ach in newly_unlocked:
        print(f"  Newly unlocked and notified: {ach['name']}")
    assert len(newly_unlocked) > 0
    newly_unlocked_again = reward_mod.get_unlocked_achievements_and_clear_notifications()
    assert len(newly_unlocked_again) == 0 # Should be empty now

    print("\nReward Module test complete.")

