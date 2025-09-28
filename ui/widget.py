"""UI Widget Module for GameBuddy Focus Tracker.
Provides the overlay widget for displaying metrics and feedback.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QSlider, QComboBox,
                            QFrame, QSizePolicy, QMenu)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QColor, QPalette, QFont, QIcon, QAction, QCursor

class Widget(QWidget):
    """Overlay widget for GameBuddy Focus Tracker."""
    
    # Signal to notify main app of settings changes
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the widget.
        
        Args:
            parent: Parent widget, if any.
        """
        super().__init__(parent)
        
        # Widget state
        self.dragging = False
        self.drag_position = QPoint()
        self.opacity_mode = "translucent"  # "transparent", "translucent", "opaque"
        self.expanded = True
        self.metrics = {
            "attention": 0,
            "fatigue": 0,
            "frustration": 0,
            "distraction": 0
        }
        self.buddy_message = "Ready to track your focus!"
        self.current_mood = "neutral"
        self.mood_emojis = {
            "focused": "😊",  # Happy/focused
            "tired": "😴",    # Tired/sleepy
            "frustrated": "😠", # Angry/frustrated
            "distracted": "🤔", # Thinking/distracted
            "neutral": "😐"   # Neutral
        }
        
        # Setup UI
        self.setup_ui()
        
        # Set default position (top-right corner with some margin)
        screen_geometry = self.screen().geometry()
        self.move(screen_geometry.width() - self.width() - 20, 20)
        
        # Set window flags for overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Set window opacity based on mode
        self.set_opacity_mode(self.opacity_mode)
        
        # Show the widget
        self.show()
    
    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)
        
        # Title bar with controls
        self.setup_title_bar()
        
        # Mood status
        self.setup_mood_status()
        
        # Metrics display
        self.setup_metrics_display()
        
        # Buddy message
        self.setup_buddy_message()
        
        # Set initial size
        self.setMinimumWidth(300)
        self.adjustSize()
        
        # Apply styling
        self.apply_styling()
    
    def setup_title_bar(self):
        """Set up the title bar with controls."""
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("GameBuddy Focus Tracker")
        title_label.setObjectName("title_label")
        title_bar.addWidget(title_label)
        
        # Spacer
        title_bar.addStretch()
        
        # Settings button
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("control_button")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.show_settings_menu)
        title_bar.addWidget(self.settings_btn)
        
        # Minimize button
        self.minimize_btn = QPushButton("_")
        self.minimize_btn.setObjectName("control_button")
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self.toggle_expanded)
        title_bar.addWidget(self.minimize_btn)
        
        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("control_button")
        self.close_btn.setToolTip("Hide")
        self.close_btn.clicked.connect(self.hide)
        title_bar.addWidget(self.close_btn)
        
        self.main_layout.addLayout(title_bar)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(separator)
    
    def setup_mood_status(self):
        """Set up the mood status display."""
        self.mood_layout = QHBoxLayout()
        
        # Mood label
        mood_label = QLabel("Mood Status:")
        mood_label.setObjectName("section_label")
        self.mood_layout.addWidget(mood_label)
        
        # Mood emoji
        self.mood_emoji_label = QLabel(self.mood_emojis["neutral"])
        self.mood_emoji_label.setObjectName("mood_emoji")
        self.mood_layout.addWidget(self.mood_emoji_label)
        
        # Mood text
        self.mood_text_label = QLabel("Neutral")
        self.mood_text_label.setObjectName("mood_text")
        self.mood_layout.addWidget(self.mood_text_label)
        
        # Add stretch to push everything to the left
        self.mood_layout.addStretch()
        
        self.main_layout.addLayout(self.mood_layout)
    
    def setup_metrics_display(self):
        """Set up the metrics display with progress bars."""
        self.metrics_layout = QVBoxLayout()
        self.metrics_layout.setSpacing(8)
        
        # Create progress bars for each metric
        self.progress_bars = {}
        
        # Attention
        attention_layout = QHBoxLayout()
        attention_label = QLabel("Attention:")
        attention_label.setObjectName("metric_label")
        attention_layout.addWidget(attention_label)
        
        self.progress_bars["attention"] = QProgressBar()
        self.progress_bars["attention"].setObjectName("attention_bar")
        self.progress_bars["attention"].setRange(0, 100)
        self.progress_bars["attention"].setValue(0)
        attention_layout.addWidget(self.progress_bars["attention"])
        
        self.metrics_layout.addLayout(attention_layout)
        
        # Fatigue
        fatigue_layout = QHBoxLayout()
        fatigue_label = QLabel("Fatigue:")
        fatigue_label.setObjectName("metric_label")
        fatigue_layout.addWidget(fatigue_label)
        
        self.progress_bars["fatigue"] = QProgressBar()
        self.progress_bars["fatigue"].setObjectName("fatigue_bar")
        self.progress_bars["fatigue"].setRange(0, 100)
        self.progress_bars["fatigue"].setValue(0)
        fatigue_layout.addWidget(self.progress_bars["fatigue"])
        
        self.metrics_layout.addLayout(fatigue_layout)
        
        # Frustration
        frustration_layout = QHBoxLayout()
        frustration_label = QLabel("Frustration:")
        frustration_label.setObjectName("metric_label")
        frustration_layout.addWidget(frustration_label)
        
        self.progress_bars["frustration"] = QProgressBar()
        self.progress_bars["frustration"].setObjectName("frustration_bar")
        self.progress_bars["frustration"].setRange(0, 100)
        self.progress_bars["frustration"].setValue(0)
        frustration_layout.addWidget(self.progress_bars["frustration"])
        
        self.metrics_layout.addLayout(frustration_layout)
        
        # Distraction
        distraction_layout = QHBoxLayout()
        distraction_label = QLabel("Distraction:")
        distraction_label.setObjectName("metric_label")
        distraction_layout.addWidget(distraction_label)
        
        self.progress_bars["distraction"] = QProgressBar()
        self.progress_bars["distraction"].setObjectName("distraction_bar")
        self.progress_bars["distraction"].setRange(0, 100)
        self.progress_bars["distraction"].setValue(0)
        distraction_layout.addWidget(self.progress_bars["distraction"])
        
        self.metrics_layout.addLayout(distraction_layout)
        
        self.main_layout.addLayout(self.metrics_layout)
    
    def setup_buddy_message(self):
        """Set up the buddy message display."""
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(separator)
        
        # Buddy message
        self.buddy_message_label = QLabel(self.buddy_message)
        self.buddy_message_label.setObjectName("buddy_message")
        self.buddy_message_label.setWordWrap(True)
        self.buddy_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.buddy_message_label)
    
    def apply_styling(self):
        """Apply CSS styling to the widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
                border-radius: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            #title_label {
                font-size: 14px;
                font-weight: bold;
                color: #FFFFFF;
            }
            
            #control_button {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-size: 14px;
                padding: 2px;
                min-width: 20px;
                max-width: 20px;
            }
            
            #control_button:hover {
                color: #FFFFFF;
            }
            
            #section_label, #metric_label {
                font-size: 12px;
                min-width: 80px;
            }
            
            #mood_emoji {
                font-size: 18px;
            }
            
            #mood_text {
                font-size: 12px;
                color: #CCCCCC;
            }
            
            #buddy_message {
                font-size: 13px;
                color: #E0E0E0;
                padding: 5px;
                background-color: #3E3E42;
                border-radius: 5px;
            }
            
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 5px;
                text-align: center;
                height: 15px;
                background-color: #3E3E42;
            }
            
            QProgressBar::chunk {
                border-radius: 5px;
            }
            
            #attention_bar::chunk {
                background-color: #4CAF50;  /* Green */
            }
            
            #fatigue_bar::chunk {
                background-color: #FF9800;  /* Orange */
            }
            
            #frustration_bar::chunk {
                background-color: #F44336;  /* Red */
            }
            
            #distraction_bar::chunk {
                background-color: #2196F3;  /* Blue */
            }
        """)
    
    def update_metrics(self, metrics):
        """Update the displayed metrics.
        
        Args:
            metrics (dict): Dictionary containing the metrics to display.
        """
        self.metrics = metrics
        
        # Update progress bars
        for metric, value in metrics.items():
            if metric in self.progress_bars:
                self.progress_bars[metric].setValue(int(value))
                
                # Update progress bar color based on value
                if metric == "attention":
                    self.update_bar_color(metric, value, "high_good")
                else:
                    self.update_bar_color(metric, value, "low_good")
        
        # Determine mood based on metrics
        self.update_mood()
    
    def update_bar_color(self, metric, value, mode="high_good"):
        """Update the color of a progress bar based on its value.
        
        Args:
            metric (str): The metric name.
            value (float): The metric value.
            mode (str): "high_good" if high values are good, "low_good" if low values are good.
        """
        bar = self.progress_bars[metric]
        
        if mode == "high_good":
            if value >= 70:
                color = "#4CAF50"  # Green
            elif value >= 40:
                color = "#FFC107"  # Yellow
            else:
                color = "#F44336"  # Red
        else:  # low_good
            if value <= 30:
                color = "#4CAF50"  # Green
            elif value <= 60:
                color = "#FFC107"  # Yellow
            else:
                color = "#F44336"  # Red
        
        # Apply the color
        bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
    
    def update_mood(self):
        """Update the mood status based on current metrics."""
        # Simple logic to determine mood
        attention = self.metrics.get("attention", 0)
        fatigue = self.metrics.get("fatigue", 0)
        frustration = self.metrics.get("frustration", 0)
        distraction = self.metrics.get("distraction", 0)
        
        # Determine the dominant mood
        if frustration > 60:
            mood = "frustrated"
            mood_text = "Frustrated"
        elif fatigue > 60:
            mood = "tired"
            mood_text = "Tired"
        elif distraction > 60:
            mood = "distracted"
            mood_text = "Distracted"
        elif attention > 70:
            mood = "focused"
            mood_text = "Focused"
        else:
            mood = "neutral"
            mood_text = "Neutral"
        
        # Update the mood display
        self.current_mood = mood
        self.mood_emoji_label.setText(self.mood_emojis[mood])
        self.mood_text_label.setText(mood_text)
    
    def update_buddy_message(self, message):
        """Update the buddy message.
        
        Args:
            message (str): The new buddy message to display.
        """
        self.buddy_message = message
        self.buddy_message_label.setText(message)
    
    def update_status_message(self, message):
        """Update the status message (used when no face is detected, etc.).
        
        Args:
            message (str): The status message to display.
        """
        # For now, we'll just use the buddy message area
        self.update_buddy_message(message)
    
    def update_rewards(self, achievements):
        """Update the displayed rewards/achievements.
        
        Args:
            achievements (list): List of achievements to display.
        """
        # This is a placeholder for future implementation
        # Could add a small icon or notification for achievements
        pass
    
    def set_opacity_mode(self, mode):
        """Set the opacity mode of the widget.
        
        Args:
            mode (str): The opacity mode ("transparent", "translucent", "opaque").
        """
        self.opacity_mode = mode
        
        if mode == "transparent":
            # Only show the progress bars and labels
            self.setWindowOpacity(0.7)
            # Hide non-essential elements
            self.buddy_message_label.setVisible(False)
            # Could add more hiding logic here
        elif mode == "translucent":
            # Semi-transparent
            self.setWindowOpacity(0.85)
            # Show all elements
            self.buddy_message_label.setVisible(True)
        else:  # opaque
            # Fully visible
            self.setWindowOpacity(1.0)
            # Show all elements
            self.buddy_message_label.setVisible(True)
    
    def toggle_expanded(self):
        """Toggle between expanded and minimized states."""
        self.expanded = not self.expanded
        
        if self.expanded:
            # Expand the widget
            self.minimize_btn.setText("_")
            # Show all elements
            for i in range(self.metrics_layout.count()):
                item = self.metrics_layout.itemAt(i)
                if item:
                    item.layout().itemAt(1).widget().setVisible(True)
            self.buddy_message_label.setVisible(True)
        else:
            # Minimize the widget (show only labels)
            self.minimize_btn.setText("□")
            # Hide progress bars but keep labels
            for i in range(self.metrics_layout.count()):
                item = self.metrics_layout.itemAt(i)
                if item:
                    item.layout().itemAt(1).widget().setVisible(False)
            self.buddy_message_label.setVisible(False)
        
        # Adjust size
        self.adjustSize()
    
    def show_settings_menu(self):
        """Show the settings menu."""
        menu = QMenu(self)
        
        # Opacity modes
        opacity_menu = menu.addMenu("Display Mode")
        
        transparent_action = QAction("Transparent", self)
        transparent_action.triggered.connect(lambda: self.set_opacity_mode("transparent"))
        opacity_menu.addAction(transparent_action)
        
        translucent_action = QAction("Translucent", self)
        translucent_action.triggered.connect(lambda: self.set_opacity_mode("translucent"))
        opacity_menu.addAction(translucent_action)
        
        opaque_action = QAction("Opaque", self)
        opaque_action.triggered.connect(lambda: self.set_opacity_mode("opaque"))
        opacity_menu.addAction(opaque_action)
        
        # Reset position
        reset_pos_action = QAction("Reset Position", self)
        reset_pos_action.triggered.connect(self.reset_position)
        menu.addAction(reset_pos_action)
        
        # Show the menu at the button's position
        menu.exec(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft()))
    
    def reset_position(self):
        """Reset the widget position to the top-right corner."""
        screen_geometry = self.screen().geometry()
        self.move(screen_geometry.width() - self.width() - 20, 20)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for dragging.
        
        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging.
        
        Args:
            event: The mouse event.
        """
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging.
        
        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

if __name__ == "__main__":
    # Test the widget
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    widget = Widget()
    
    # Test with some sample metrics
    widget.update_metrics({
        "attention": 75,
        "fatigue": 30,
        "frustration": 15,
        "distraction": 25
    })
    
    widget.update_buddy_message("You're doing great! Keep that focus up.")
    
    sys.exit(app.exec())
