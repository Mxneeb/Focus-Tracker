"""Main entry point for the GameBuddy Focus Tracker application."""

# Import core modules
from core import input_module, cv_module, metric_module, state_module, feedback_module
from core import adaptive_coaching_module, reward_module
from ui import widget, settings_panel
from data import storage_manager
from config import app_config

import time
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

class GameBuddyApp:
    """Main application class for GameBuddy Focus Tracker."""
    def __init__(self):
        """Initialize all modules."""
        print("Initializing GameBuddy Focus Tracker...")
        
        # Initialize PyQt application
        self.qt_app = QApplication(sys.argv)
        
        # Initialize configuration
        self.config = app_config.AppConfig()
        
        # Initialize core modules
        self.input_source = input_module.InputModule(source_id=self.config.get_setting("camera_id", 0))
        self.cv_processor = cv_module.CVModule()
        self.metric_calculator = metric_module.MetricModule()
        self.state_classifier = state_module.StateModule()
        self.feedback_provider = feedback_module.FeedbackModule()
        self.coach = adaptive_coaching_module.AdaptiveCoachingModule()
        self.rewards = reward_module.RewardModule()
        self.storage = storage_manager.StorageManager(db_path=self.config.get_setting("database_path", "data/gamebuddy.db"))
        
        # Initialize UI
        self.main_widget = widget.Widget()
        self.settings_ui = None  # Placeholder for settings_panel.SettingsPanel()
        
        # Set up timer for processing loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.setInterval(self.config.get_setting("loop_delay_ms", 500))  # Default to 500ms (2 FPS)
        
        print("GameBuddy Focus Tracker initialized.")

    def run(self):
        """Start the application and event loop."""
        print("Starting GameBuddy Focus Tracker main loop...")
        
        # Start the processing timer
        self.timer.start()
        
        # Start the Qt event loop
        return self.qt_app.exec()

    def process_frame(self):
        """Process a single frame and update metrics."""
        try:
            # 1. Get frame from input module
            frame = self.input_source.get_frame()
            if frame is None:
                print("No frame received, ending loop.")
                self.timer.stop()
                return

            # 2. Process frame with CV module
            cv_data = self.cv_processor.process_frame(frame)
            if not cv_data:
                # Update UI to show no face detected
                if self.main_widget:
                    self.main_widget.update_status_message("No face detected")
                return

            # 3. Calculate metrics
            # Check if the metric_calculator expects the current_frame_time_for_sim parameter
            import inspect
            sig = inspect.signature(self.metric_calculator.calculate_metrics)
            if 'current_frame_time_for_sim' in sig.parameters:
                # If it does, provide the current time
                metrics = self.metric_calculator.calculate_metrics(cv_data, time.time())
            else:
                # Otherwise use the standard signature
                metrics = self.metric_calculator.calculate_metrics(cv_data)

            # 4. Classify state
            current_state = self.state_classifier.classify_state(metrics)

            # 5. Adaptive coaching (optional, based on state and history)
            self.coach.update(current_state, metrics)

            # 6. Reward system (optional)
            self.rewards.update(current_state, metrics)

            # 7. Get feedback message
            feedback_message = self.feedback_provider.get_message(current_state)
            # Potentially modify message based on adaptive coaching
            feedback_message = self.coach.adapt_message(feedback_message, current_state)

            # 8. Update UI Widget
            if self.main_widget:
                self.main_widget.update_metrics(metrics)
                self.main_widget.update_buddy_message(feedback_message)
                self.main_widget.update_rewards(self.rewards.get_achievements())
            else:
                # Placeholder for console output if no UI
                print(f"Metrics: {metrics}")
                print(f"State: {current_state}")
                print(f"Message: {feedback_message}")

            # 9. Store data (optional, for history/patterns)
            self.storage.log_data(timestamp=time.time(), metrics=metrics, state=current_state)

        except Exception as e:
            print(f"Error in processing frame: {e}")

    def shutdown(self):
        """Clean up resources."""
        print("Shutting down GameBuddy Focus Tracker...")
        # Stop the timer
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        
        # Release resources
        if hasattr(self, 'input_source'):
            self.input_source.release()
        
        # Close storage
        if hasattr(self, 'storage'):
            self.storage.close()
        
        print("Shutdown complete.")

def main():
    """Main function to start the application."""
    app = GameBuddyApp()
    
    # Set up exception handling to ensure proper shutdown
    try:
        exit_code = app.run()
    except KeyboardInterrupt:
        print("GameBuddy Focus Tracker stopped by user.")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        app.shutdown()
        sys.exit(exit_code if 'exit_code' in locals() else 1)

if __name__ == "__main__":
    main()
