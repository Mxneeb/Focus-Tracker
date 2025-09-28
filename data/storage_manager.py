"""Data Storage Module for GameBuddy Focus Tracker.
Handles saving and loading of application data (metrics, patterns, rewards, settings).
"""

import sqlite3
import json
import os
import time

class StorageManager:
    """Manages local data storage using SQLite."""
    def __init__(self, db_path="data/gamebuddy.db"):
        """Initialize the storage manager and database.
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._ensure_db_dir_exists()
        self.conn = None
        self.cursor = None
        self._connect_db()
        self._create_tables()
        print(f"Storage Manager initialized with DB: {self.db_path}")

    def _ensure_db_dir_exists(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"Created data directory: {db_dir}")

    def _connect_db(self):
        """Connects to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database {self.db_path}: {e}")
            self.conn = None
            self.cursor = None

    def _create_tables(self):
        """Creates necessary tables if they don't exist."""
        if not self.cursor:
            print("Cannot create tables, no database cursor.")
            return

        try:
            # Table for historical metrics and states
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS metric_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    attention INTEGER,
                    fatigue INTEGER,
                    frustration INTEGER,
                    engagement INTEGER,
                    distraction INTEGER,
                    classified_state TEXT
                )
            """)

            # Table for adaptive coaching patterns (storing as JSON blobs for flexibility)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS adaptive_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT UNIQUE NOT NULL, -- e.g., "frustration_triggers", "fatigue_onset_times"
                    pattern_data TEXT -- JSON string
                )
            """)

            # Table for reward system data (achievements progress)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reward_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    achievement_key TEXT UNIQUE NOT NULL,
                    achievement_details TEXT -- JSON string of name, desc, unlocked, progress, target, notified
                )
            """)
            
            # Table for general application settings (though AppConfig handles file-based for now)
            # This could be an alternative or supplement
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            self.conn.commit()
            print("Database tables ensured.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def log_data(self, timestamp, metrics, state):
        """Logs metric data and classified state to the database."""
        if not self.cursor:
            print("Cannot log data, no database cursor.")
            return
        try:
            self.cursor.execute("""
                INSERT INTO metric_logs (timestamp, attention, fatigue, frustration, engagement, distraction, classified_state)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, metrics.get("attention"), metrics.get("fatigue"), metrics.get("frustration"), 
                  metrics.get("engagement"), metrics.get("distraction"), state))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error logging metrics: {e}")

    def save_adaptive_patterns(self, patterns_data):
        """Saves adaptive coaching patterns (e.g., frustration_triggers)."""
        if not self.cursor:
            return
        try:
            for p_type, data in patterns_data.items():
                self.cursor.execute("""
                    INSERT OR REPLACE INTO adaptive_patterns (pattern_type, pattern_data)
                    VALUES (?, ?)
                """, (p_type, json.dumps(data)))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving adaptive patterns: {e}")

    def load_adaptive_patterns(self):
        """Loads all adaptive coaching patterns."""
        if not self.cursor:
            return None
        try:
            self.cursor.execute("SELECT pattern_type, pattern_data FROM adaptive_patterns")
            rows = self.cursor.fetchall()
            patterns = {row[0]: json.loads(row[1]) for row in rows}
            return patterns if patterns else None
        except sqlite3.Error as e:
            print(f"Error loading adaptive patterns: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for adaptive patterns: {e}")
            return None

    def save_reward_data(self, achievements_data):
        """Saves reward system data (achievements)."""
        if not self.cursor:
            return
        try:
            for ach_key, details in achievements_data.items():
                self.cursor.execute("""
                    INSERT OR REPLACE INTO reward_data (achievement_key, achievement_details)
                    VALUES (?, ?)
                """, (ach_key, json.dumps(details)))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving reward data: {e}")

    def load_reward_data(self):
        """Loads reward system data (achievements)."""
        if not self.cursor:
            return None
        try:
            self.cursor.execute("SELECT achievement_key, achievement_details FROM reward_data")
            rows = self.cursor.fetchall()
            achievements = {row[0]: json.loads(row[1]) for row in rows}
            return achievements if achievements else None
        except sqlite3.Error as e:
            print(f"Error loading reward data: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for reward data: {e}")
            return None

    # Example for app_settings table (if used over file config for some settings)
    def save_setting(self, key, value):
        if not self.cursor: return
        try:
            self.cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving setting 	'{key}	': {e}")

    def load_setting(self, key, default=None):
        if not self.cursor: return default
        try:
            self.cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = self.cursor.fetchone()
            return json.loads(row[0]) if row else default
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"Error loading setting 	'{key}	': {e}")
            return default

    def get_recent_metric_logs(self, limit=100):
        """Retrieves recent metric logs."""
        if not self.cursor: return []
        try:
            self.cursor.execute(f"SELECT * FROM metric_logs ORDER BY timestamp DESC LIMIT {limit}")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching metric logs: {e}")
            return []

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            print("Database connection closed.")

if __name__ == "__main__":
    print("Testing Storage Manager...")
    # Use a temporary DB for testing
    test_db_path = "data/test_gamebuddy.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    storage = StorageManager(db_path=test_db_path)

    # Test logging
    print("\nTesting metric logging...")
    mock_metrics = {"attention": 80, "fatigue": 20, "frustration": 10, "engagement": 70, "distraction": 15}
    storage.log_data(time.time(), mock_metrics, "Focused")
    storage.log_data(time.time() + 1, {**mock_metrics, "attention": 30, "frustration": 70}, "Highly Frustrated")
    logs = storage.get_recent_metric_logs(5)
    print(f"Retrieved {len(logs)} logs. Last log state: {logs[0][-1] if logs else 'N/A'}")
    assert len(logs) == 2

    # Test adaptive patterns
    print("\nTesting adaptive patterns save/load...")
    test_patterns = {"frustration_triggers": [{"ts": time.time(), "context": "boss_fight"}]}
    storage.save_adaptive_patterns(test_patterns)
    loaded_patterns = storage.load_adaptive_patterns()
    print(f"Loaded patterns: {loaded_patterns}")
    assert loaded_patterns["frustration_triggers"][0]["context"] == "boss_fight"

    # Test reward data
    print("\nTesting reward data save/load...")
    test_rewards = {"focus_streak_10m": {"name": "Focused Mind", "unlocked": True, "progress": 600, "target": 600}}
    storage.save_reward_data(test_rewards)
    loaded_rewards = storage.load_reward_data()
    print(f"Loaded rewards: {loaded_rewards}")
    assert loaded_rewards["focus_streak_10m"]["unlocked"] == True

    # Test settings (if using DB for settings)
    print("\nTesting settings save/load...")
    storage.save_setting("user_name", "Gamer123")
    user_name = storage.load_setting("user_name")
    print(f"Loaded user_name: {user_name}")
    assert user_name == "Gamer123"
    non_existent = storage.load_setting("non_existent_setting", "default_val")
    assert non_existent == "default_val"

    storage.close()
    # Clean up test DB
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        # Also remove data directory if it became empty
        try:
            if not os.listdir(os.path.dirname(test_db_path)):
                 os.rmdir(os.path.dirname(test_db_path))
        except OSError:
            pass # Fine if it couldn't be removed (e.g. not empty due to other files)

    print("\nStorage Manager test complete.")

