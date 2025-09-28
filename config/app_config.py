"""Configuration module for GameBuddy Focus Tracker."""

import json
import os

DEFAULT_CONFIG_PATH = "config/default_config.json"
USER_CONFIG_PATH = "config/user_config.json" # User-specific overrides

class AppConfig:
    """Handles application configuration."""
    def __init__(self, default_path=DEFAULT_CONFIG_PATH, user_path=USER_CONFIG_PATH):
        self.default_config_path = os.path.join(os.path.dirname(__file__), "..", default_path) # Adjust path relative to this file
        self.user_config_path = os.path.join(os.path.dirname(__file__), "..", user_path)
        self.config = {}
        self._load_config()

    def _ensure_config_dir_exists(self):
        config_dir = os.path.dirname(self.user_config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            print(f"Created config directory: {config_dir}")

    def _create_default_config_if_not_exists(self):
        default_dir = os.path.dirname(self.default_config_path)
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
            print(f"Created default config directory: {default_dir}")

        if not os.path.exists(self.default_config_path):
            print(f"Default config not found at {self.default_config_path}, creating one.")
            default_settings = {
                "camera_id": 0,
                "loop_delay_seconds": 0.5, # Approx 2 FPS for main loop
                "database_path": "data/gamebuddy.db",
                "log_level": "INFO",
                "ui_theme": "dark",
                "widget_position": "top_right",
                "widget_transparency": 0.8,
                # Add other default settings here
                "metrics": {
                    "attention_weights": {"gaze": 0.4, "time_on_screen": 0.3, "head_pose": 0.2, "engagement": 0.1},
                    "fatigue_weights": {"yawn": 0.3, "perclos": 0.4, "eye_closure": 0.2, "head_droop": 0.1}
                },
                "adaptive_coaching_enabled": True,
                "reward_system_enabled": True
            }
            try:
                with open(self.default_config_path, "w") as f:
                    json.dump(default_settings, f, indent=4)
                print(f"Created default config file at {self.default_config_path}")
            except IOError as e:
                print(f"Error creating default config file: {e}")
                # Fallback to in-memory defaults if file creation fails
                self.config = default_settings

    def _load_config(self):
        """Loads configuration from default and user-specific files."""
        self._ensure_config_dir_exists()
        self._create_default_config_if_not_exists()

        # Load default config
        try:
            with open(self.default_config_path, "r") as f:
                self.config = json.load(f)
            print(f"Loaded default configuration from {self.default_config_path}")
        except FileNotFoundError:
            print(f"Warning: Default config file not found at {self.default_config_path}. Using hardcoded defaults.")
            # This part should ideally not be reached if _create_default_config_if_not_exists works
            self.config = {
                "camera_id": 0, "loop_delay_seconds": 0.5, "database_path": "data/gamebuddy.db",
                "log_level": "INFO", "ui_theme": "dark", "widget_position": "top_right",
                "widget_transparency": 0.8,
                "metrics": {
                    "attention_weights": {"gaze": 0.4, "time_on_screen": 0.3, "head_pose": 0.2, "engagement": 0.1},
                    "fatigue_weights": {"yawn": 0.3, "perclos": 0.4, "eye_closure": 0.2, "head_droop": 0.1}
                },
                "adaptive_coaching_enabled": True,
                "reward_system_enabled": True
            }
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {self.default_config_path}. Using hardcoded defaults.")
            self.config = {}
        except IOError as e:
            print(f"Error reading default config file {self.default_config_path}: {e}. Using hardcoded defaults.")
            self.config = {}


        # Override with user config if it exists
        try:
            with open(self.user_config_path, "r") as f:
                user_specific_config = json.load(f)
                self.config.update(user_specific_config)
                print(f"Loaded and merged user configuration from {self.user_config_path}")
        except FileNotFoundError:
            print(f"User config file not found at {self.user_config_path}. Using default/loaded configuration.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {self.user_config_path}. User settings not applied.")
        except IOError as e:
            print(f"Error reading user config file {self.user_config_path}: {e}. User settings not applied.")

    def get_setting(self, key, default=None):
        """Retrieves a setting value."""
        # Allow nested key access e.g., "metrics.attention_weights"
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            # print(f"Warning: Setting 	'{key}	' not found, returning default: {default}")
            return default
        except TypeError: # If a parent key is not a dict
            # print(f"Warning: Setting 	'{key}	' path invalid, returning default: {default}")
            return default

    def set_setting(self, key, value):
        """Sets a setting value and saves it to the user config file."""
        # Allow nested key access
        keys = key.split(".")
        d = self.config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        
        self._save_user_config()

    def _save_user_config(self):
        """Saves the current configuration (user-specific parts) to the user file."""
        # We only want to save settings that differ from default or are user-added
        # For simplicity here, we save the parts of self.config that might have been user-modified.
        # A more robust way would be to track only user-set values.
        user_settings_to_save = {}
        try:
            with open(self.user_config_path, "r") as f:
                user_settings_to_save = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass # Start with empty or whatever was loaded
        
        # Update with current config state that might be user-modified
        # This is a simplification; ideally, we'd only save what the user explicitly changed.
        current_user_visible_config = {k: v for k, v in self.config.items() 
                                       if k not in self._get_default_keys()} 
                                       # Or more simply, just save all if not too complex

        # For nested settings, we need to be careful. Let's just save the whole current config
        # as user config for now, assuming user config is the master after load.
        # This means default_config.json is only for initial defaults.
        try:
            with open(self.user_config_path, "w") as f:
                # Save the entire current config as user config, effectively making it the source of truth after first run.
                # Or, save only the diff from default if that logic is implemented.
                json.dump(self.config, f, indent=4)
            print(f"Saved user configuration to {self.user_config_path}")
        except IOError as e:
            print(f"Error saving user configuration: {e}")

    def _get_default_keys(self):
        """Helper to get keys from the default config for diffing (not fully used above)."""
        try:
            with open(self.default_config_path, "r") as f:
                return json.load(f).keys()
        except: 
            return []

if __name__ == "__main__":
    # Test the config module
    config = AppConfig(default_path="../../config/default_config.json", user_path="../../config/user_config.json")
    print("Current Camera ID:", config.get_setting("camera_id"))
    print("Loop Delay:", config.get_setting("loop_delay_seconds"))
    print("Attention Weights:", config.get_setting("metrics.attention_weights.gaze"))
    
    config.set_setting("camera_id", 1)
    config.set_setting("metrics.new_metric.value", 100)
    print("New Camera ID:", config.get_setting("camera_id"))
    print("New Metric Value:", config.get_setting("metrics.new_metric.value"))

    # Test non-existent key
    print("Non-existent key (with default):", config.get_setting("non_existent_key", "default_val"))
    print("Non-existent nested key (with default):", config.get_setting("non.existent.key", "default_nested_val"))

    # Create a dummy default config for testing if it doesn't exist
    # Ensure the paths in __main__ are correct if running this file directly for testing
    # The paths in __init__ are relative to the gamebuddy_focus_tracker/config directory when imported.
    # If running app_config.py directly, it's in gamebuddy_focus_tracker/config, so ../../config/ is wrong.
    # It should be just "default_config.json" and "user_config.json" if running from within the config dir.
    # The provided __main__ test assumes it's run from a different location or paths are adjusted.
    # For now, the paths in __init__ are designed for when main.py imports it.

