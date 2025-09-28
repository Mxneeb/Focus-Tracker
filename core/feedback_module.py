"""Feedback Module for GameBuddy Focus Tracker.
Provides coaching messages based on the user's state.
"""

import random

class FeedbackModule:
    """Generates feedback messages based on user state."""
    def __init__(self, config=None):
        """Initialize the feedback module.
        Args:
            config (AppConfig, optional): Application configuration. Defaults to None.
        """
        self.config = config
        self.messages = {
            "Highly Focused & Engaged": [
                "You're all set and ready to win! Keep that energy up!",
                "In the zone! Amazing focus!",
                "Crushing it! Your engagement is top-tier!"
            ],
            "Focused": [
                "Great focus! Keep it steady.",
                "Looking sharp and focused!",
                "Maintaining good concentration. Well done!"
            ],
            "Slightly Distracted": [
                "Eyes off the prize! Focus up, champion.",
                "A little distracted? Bring your attention back to the game.",
                "Regain that laser focus!"
            ],
            "Highly Distracted": [
                "Losing focus! Try to minimize distractions.",
                "Major distraction detected. Time to refocus hard!",
                "Zone back in! The game needs your full attention."
            ],
            "Slightly Fatigued": [
                "Feeling tired? A quick stretch will power you up!",
                "Energy levels dipping a bit? Consider a short break soon.",
                "A little fatigue setting in. Stay mindful of your energy."
            ],
            "Highly Fatigued": [
                "Fatigue is high. Consider taking a break to refresh!",
                "Seriously tired. A proper break is highly recommended!",
                "Don't push through extreme fatigue. Rest and come back stronger!"
            ],
            "Slightly Frustrated": [
                "Feeling a bit tense? Remember to breathe.",
                "A little frustration? Take a deep breath and reset.",
                "Keep cool. You can overcome this challenge."
            ],
            "Highly Frustrated": [
                "Game getting tough? Take a walk outside and return stronger.",
                "High frustration! Step away for a moment to clear your head.",
                "Deep breaths. Don't let frustration take over. A short break might help."
            ],
            "Neutral/Calm": [
                "Stay cool and collected.",
                "Maintaining a calm focus.",
                "Ready for whatever comes next."
            ],
            "Unknown": [
                "Monitoring your focus...",
                "Getting a read on your gaming state."
            ]
        }
        self.last_message_for_state = {}
        self.message_cooldown_seconds = self.config.get_setting("feedback.message_cooldown_seconds", 60) if self.config else 60
        print("Feedback Module initialized.")

    def get_message(self, current_state):
        """Gets an appropriate message for the current state, avoiding repetition.

        Args:
            current_state (str): The user's current classified state.

        Returns:
            str: A feedback message.
        """
        if not current_state or current_state not in self.messages:
            current_state = "Unknown"
        
        possible_messages = self.messages[current_state]
        
        # Basic cooldown logic: don't repeat the same message type too quickly
        # More advanced would be per-category cooldowns
        current_time = time.time()
        if current_state in self.last_message_for_state and \
           (current_time - self.last_message_for_state[current_state]["time"]) < self.message_cooldown_seconds and \
           len(possible_messages) > 1: # Only apply cooldown if there are other options
            # If on cooldown for this state, prefer not to show a message or show a generic one
            # For now, let's just pick one, but avoid the *exact* last message if possible
            last_msg_text = self.last_message_for_state[current_state]["text"]
            selectable_messages = [msg for msg in possible_messages if msg != last_msg_text]
            if not selectable_messages: # All messages for this state are the same as last one
                chosen_message = random.choice(possible_messages)
            else:
                chosen_message = random.choice(selectable_messages)
        else:
            chosen_message = random.choice(possible_messages)
        
        self.last_message_for_state[current_state] = {"text": chosen_message, "time": current_time}
        return chosen_message

import time # Add this if not already imported at the top

if __name__ == "__main__":
    print("Testing Feedback Module...")
    feedback_mod = FeedbackModule()

    states_to_test = [
        "Highly Focused & Engaged", "Focused", "Slightly Distracted", "Highly Distracted",
        "Slightly Fatigued", "Highly Fatigued", "Slightly Frustrated", "Highly Frustrated",
        "Neutral/Calm", "Unknown"
    ]

    for state in states_to_test:
        print(f"\nState: {state}")
        for i in range(3): # Get a few messages for each state to see variety/cooldown
            message = feedback_mod.get_message(state)
            print(f"  Attempt {i+1}: {message}")
            if i < 2: # Simulate some time passing for cooldown effect
                # feedback_mod.last_message_for_state[state]["time"] -= (feedback_mod.message_cooldown_seconds / 2) # Partial cooldown
                pass # For this test, let it pick; actual cooldown is time-based

    print("\nTesting cooldown effect for 'Highly Frustrated':")
    state = "Highly Frustrated"
    msg1 = feedback_mod.get_message(state)
    print(f"Msg 1: {msg1}")
    # Simulate getting message again immediately (should be different if possible, or same if only one option)
    msg2 = feedback_mod.get_message(state)
    print(f"Msg 2 (immediate): {msg2}") 
    # Simulate time passing beyond cooldown
    if state in feedback_mod.last_message_for_state:
         feedback_mod.last_message_for_state[state]["time"] = time.time() - (feedback_mod.message_cooldown_seconds + 5)
    msg3 = feedback_mod.get_message(state)
    print(f"Msg 3 (after cooldown): {msg3}")

    print("\nFeedback Module test complete.")

