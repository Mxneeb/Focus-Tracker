# GameBuddy Focus Tracker: Feature and Behavior Specification

**Version:** 1.0
**Date:** May 15, 2025

## 1. Introduction and Project Goal

GameBuddy Focus Tracker is a lightweight overlay widget for gamers that uses computer vision to track the user's face and emotional state during gaming sessions. It displays live statistics such as focus, fatigue, frustration, and engagement levels as percentages, and offers personalized, encouraging, or helpful messages based on the detected mood. The goal is to provide a supportive AI gaming coach that helps users manage their gaming experience, improve focus, and recognize when to take breaks, all while ensuring minimal performance impact and respecting user privacy through local data processing.

This document details the features, behavior, technical design, and user experience of the GameBuddy Focus Tracker.

## 2. Core Concept & User Interaction Flow

*   **Real-time Stats Bar:** A compact overlay widget, typically in a screen corner, displays key metrics (Attention, Fatigue, Frustration, Engagement, Distraction) as percentages, updated every few seconds.
*   **Dynamic Motivational Messages:** Personalized coaching tips or encouraging messages pop up based on the detected mood/state. The frequency of these messages is managed to avoid distraction.
*   **Buddy Persona:** The AI feels like a supportive teammate or coach rather than just a monitor.
*   **User Control:** Users can customize widget appearance and behavior.

## 3. Key Features and Metrics

### 3.1. Tracked Metrics

Each metric is displayed as a percentage (0-100%) and contributes to the overall state assessment.

1.  **Attention Level:**
    *   **What It Tracks:** How well the user keeps their eyes on the screen/game.
    *   **Widget Feedback:** Displays as "% Attention" bar (e.g., 87%). Color-coded (Green for high, Red for low).
    *   **Algorithm Details:** See `metric_algorithms.md` (Section 3.1).

2.  **Fatigue Level:**
    *   **What It Tracks:** Signs of tiredness like yawns, droopy eyes, prolonged eye closure.
    *   **Widget Feedback:** Displays as "% Fatigue" bar. Color-coded (Green for low, Red for high). Suggests “Take a break!” or similar if high.
    *   **Algorithm Details:** See `metric_algorithms.md` (Section 3.2).

3.  **Frustration Level:**
    *   **What It Tracks:** Frowning, furrowed brows, tense jaw, and emotion classification for anger/sadness.
    *   **Widget Feedback:** Displays as "% Frustration" bar. Color-coded (Green for low, Red for high). If high → “Feeling frustrated? Take a walk outside” or “Breathe and reset.”
    *   **Algorithm Details:** See `metric_algorithms.md` (Section 3.3).

4.  **Engagement Level:**
    *   **What It Tracks:** Smiling, relaxed face, excited eyes, and emotion classification for happiness.
    *   **Widget Feedback:** Displays as "% Engagement" bar. Color-coded (Green for high, Blue/Neutral for low). If high → “You’re all set! Keep crushing it!”
    *   **Algorithm Details:** See `metric_algorithms.md` (Section 3.4).

5.  **Distraction Level:**
    *   **What It Tracks:** Looking away frequently or excessive blinking not related to fatigue.
    *   **Widget Feedback:** Displays as "% Distraction" bar. Color-coded (Green for low, Red for high). Suggests refocus tips.
    *   **Algorithm Details:** See `metric_algorithms.md` (Section 3.5).

### 3.2. State Classification and Feedback Messages

*   The system classifies the user's overall state based on the combined metrics and predefined thresholds.
*   Specific coaching messages are triggered based on the classified state.
*   **Detailed Logic & Example Messages:** See `metric_algorithms.md` (Section 4).
*   **Message Frequency:** Managed to be helpful but not distracting, with cooldown periods for similar message categories.

### 3.3. Adaptive Coaching

*   **Goal:** The AI buddy learns the user's frustration patterns and adapts messages over time for more personalized and effective coaching.
*   **Mechanism:** Initially involves simple pattern tracking (e.g., game events or times correlated with high frustration). Logs data locally for this purpose.
*   **Behavior:** Over time, suggestions may become more specific or timed more effectively based on learned patterns.

### 3.4. Reward System

*   **Goal:** Encourage positive gaming habits and focus consistency.
*   **Mechanism:** Users can unlock achievements or receive positive reinforcement based on predefined goals (e.g., "Focused for 30 minutes straight," "Managed frustration successfully 5 times").
*   **Feedback:** Notifications or visual cues within the UI for unlocked achievements.

### 3.5. User Calibration

*   **Purpose:** To personalize metric calculations by establishing baseline facial behaviors (neutral pose, blink rate, etc.).
*   **Process:** User can initiate a short calibration session where they focus on a game or task. The system records baseline data during this period.
*   **Impact:** Improves the accuracy and relevance of the calculated metrics.

### 3.6. Configuration and Customization

Users will be able to:
*   Initiate calibration.
*   Customize widget appearance: position on screen, size/scale, transparency level.
*   Manage data privacy settings (e.g., data retention for adaptive coaching).
*   Enable/disable features like adaptive coaching or the reward system.

## 4. System Architecture and Technical Implementation

### 4.1. Overview

The system is a Python-based desktop application using computer vision for real-time analysis and a lightweight GUI for the overlay widget. All processing is local.

### 4.2. Main Components

*   **Input Module (Webcam Access):** Uses OpenCV.
*   **Computer Vision (CV) Module:**
    *   Face Detection, Facial Landmarks, Head Pose: MediaPipe.
    *   Emotion Classification: DeepFace (with a lightweight backend, potential for fine-tuning).
*   **Metric Calculation Module:** Implements algorithms detailed in `metric_algorithms.md`.
*   **State Classification Module:** Implements logic from `metric_algorithms.md`.
*   **UI/UX Widget Module:** Python GUI library (Tkinter, PyQt, or Kivy - TBD). Details in `ui_ux_design.md`.
*   **Feedback & Messaging Module:** Selects messages based on state.
*   **Adaptive Coaching Module:** Learns user patterns.
*   **Reward System Module:** Tracks achievements.
*   **Local Data Storage Module:** SQLite or JSON files for calibration, patterns, rewards, preferences.
*   **Configuration Module:** Manages user settings.

**Detailed Architecture:** See `system_architecture.md`.
**Technology Research Summary:** See `research_summary_cv.md`.

### 4.3. Performance and Resource Usage

*   **Goal:** Lightweight CPU/RAM usage to run alongside games without noticeable impact.
*   **Strategies:** Efficient CV models (MediaPipe), optimized Python code, infrequent updates for less critical UI elements.

### 4.4. Data Privacy

*   All video processing, metric calculation, and data storage (calibration, patterns, rewards) are performed **strictly locally** on the user's machine.
*   No facial data or derived metrics are transmitted externally.

### 4.5. Target Platforms and Game Genres

*   **Primary Development Language:** Python.
*   **Operating Systems:** Initial focus on Windows, with potential for macOS and Linux support depending on GUI library choice and demand.
*   **Initial Game Genre Optimization:** Battle Royale/Third-Person Shooter (e.g., Fortnite) and 2D Platform Fighter (e.g., Brawlhalla).

## 5. UI/UX Design Details

*   **Widget Layout:** Compact, user-configurable position (default: screen corner).
*   **Visuals:** Clean, modern, slightly "gamified" aesthetic. Color-coded bars for metrics.
*   **Interactions:** Minimal direct interaction needed during gameplay. Settings accessible via an icon on the widget or system tray.
*   **Notifications:** Buddy messages appear in a dedicated area of the widget. Reward notifications are brief and positive.

**Detailed UI/UX Design:** See `ui_ux_design.md`.

## 6. Excluded Features (Future Considerations)

*   **Sound/Voice Feedback:** Deferred for future versions to maintain initial simplicity and low distraction.

## 7. Dependencies and Installation

*   Python 3.x
*   Libraries: OpenCV, MediaPipe, DeepFace (and its dependencies), chosen GUI library (Tkinter/PyQt/Kivy).
*   Installation will likely involve `pip install -r requirements.txt`.

## 8. Open Questions & Areas for Further Tuning

*   Optimal weights and thresholds for metric calculation and state classification will require iterative tuning and testing.
*   Specific implementation details for the overlay window (always-on-top, click-through) with the chosen GUI library.
*   Fine-tuning strategy and dataset acquisition for emotion models if default accuracy is insufficient for target game genres.

This document provides a comprehensive overview of the GameBuddy Focus Tracker. It will be updated as the project progresses and further refinements are made based on development and user feedback.
