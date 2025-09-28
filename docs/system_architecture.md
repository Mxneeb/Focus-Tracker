# GameBuddy Focus Tracker: System Architecture

## 1. Overview

The GameBuddy Focus Tracker is a desktop application designed to monitor a gamer's facial cues and emotional state in real-time, providing feedback through a lightweight overlay widget. The system will be developed primarily in Python, emphasizing low resource usage and local data processing.

## 2. Guiding Principles

*   **Modularity:** Components will be designed as distinct modules with clear interfaces to facilitate development, testing, and future upgrades.
*   **Performance:** The system must be lightweight to run alongside resource-intensive games without significant impact on performance.
*   **Local Processing:** All data, including video frames and derived metrics, will be processed and stored locally on the user's machine to ensure privacy.
*   **Real-time Feedback:** The system will provide feedback with minimal latency.
*   **User-centric Design:** The UI will be non-intrusive, and feedback messages will be supportive and coaching-oriented.

## 3. Main Components and Interactions

The system will consist of the following main components:

```mermaid
graph TD
    A[Input Module (Webcam)] --> B(CV Module);
    B --> C[Metric Calculation Module];
    C --> D[State Classification Module];
    D --> E[Feedback & Messaging Module];
    D --> F[Adaptive Coaching Module];
    D --> G[Reward System Module];
    E --> H(UI/UX Widget Module);
    F --> I[Local Data Storage Module];
    G --> I;
    C --> I; # For calibration data and historical metrics
    J[Configuration Module] --> B;
    J --> C;
    J --> H;
    J --> I;
    H --> J; # User interaction with settings
```

### 3.1. Input Module
*   **Responsibilities:** Access and capture video frames from the user's webcam.
*   **Technology:** Python libraries like OpenCV (`cv2`) will be used for camera access.
*   **Output:** Raw video frames passed to the CV Module.

### 3.2. Computer Vision (CV) Module
*   **Responsibilities:**
    *   Detect faces in the video frames.
    *   Identify facial landmarks.
    *   Estimate head pose.
    *   Analyze facial expressions to infer emotional cues (e.g., smiling, frowning, yawning, eye state).
    *   Classify primary emotions (frustration, engagement/happiness).
*   **Technology (Proposed):**
    *   **MediaPipe:** For efficient real-time face detection, detailed facial landmarking (478 landmarks), head pose estimation, and blendshape scores (useful for inferring expressions like yawns, eye droopiness, smiles).
    *   **DeepFace (with a lightweight backend like VGG-Face or a custom-trained model):** For classifying discrete emotions like frustration and happiness. This can be used to complement MediaPipe's blendshapes.
    *   **Fine-tuning:** As requested, explore options for fine-tuning emotion recognition models on relevant datasets or with user-provided feedback (long-term).
*   **Output:** Structured data including bounding box of the face, landmark coordinates, head pose angles, eye state (open/closed, blink rate), and raw emotion/expression scores.

### 3.3. Metric Calculation Module
*   **Responsibilities:** Calculate the five key metrics based on data from the CV Module:
    *   **Attention Level (%):** Weighted score combining gaze direction (derived from eye landmarks and head pose relative to an assumed screen position), time eyes are on the screen, and facial engagement. Penalties for frequent looking away or excessive blinking.
    *   **Fatigue Level (%):** Derived from signs like yawning frequency (from mouth landmarks), eye droopiness (from eye landmarks), and prolonged eye closure.
    *   **Frustration Level (%):** Based on emotion classification (e.g., DeepFace output for "angry" or "sad") and facial expressions like frowning, furrowed brows, tense jaw (from MediaPipe landmarks and blendshapes).
    *   **Engagement Level (%):** Based on emotion classification (e.g., DeepFace output for "happy") and expressions like smiling, relaxed face, excited eyes (from MediaPipe landmarks and blendshapes).
    *   **Distraction Level (%):** Calculated from frequency and duration of looking away from the screen, and potentially excessive blinking not related to fatigue.
*   **Logic:** Will use the user-provided formula for Attention and develop similar logic for other metrics. Includes optional user calibration to set personal baselines.
*   **Output:** Percentage values (0-100%) for each of the five metrics.

### 3.4. State Classification Module
*   **Responsibilities:** Interpret the calculated metrics to determine the user's overall state.
*   **Logic:** Define thresholds for each metric (e.g., Frustration > 70% triggers a specific state). Combine multiple metrics to infer more complex states if necessary.
*   **Output:** A classified user state (e.g., "Focused", "Slightly Tired", "Highly Frustrated", "Engaged", "Distracted").

### 3.5. UI/UX Widget Module
*   **Responsibilities:**
    *   Display the real-time metric percentages (e.g., as progress bars).
    *   Show the current "buddy message" from the Feedback Module.
    *   Be minimal, non-intrusive, and customizable (position, transparency).
    *   Use color coding to intuitively signal state (green for good, yellow for warning, red for critical).
*   **Technology:** Python GUI libraries like **Tkinter** (built-in, simple), **PyQt** (more features, robust), or **Kivy** (good for custom UIs, cross-platform). The choice will depend on the desired level of customization and performance. An overlay approach will be necessary, potentially using platform-specific APIs or libraries that support transparent, always-on-top windows.
*   **Input:** Metric percentages, buddy messages.

### 3.6. Feedback & Messaging Module
*   **Responsibilities:** Generate and select appropriate motivational messages or coaching tips based on the classified user state.
*   **Logic:** A predefined set of messages categorized by state. Messages should be varied and delivered with appropriate frequency to avoid being distracting, as per user feedback.
*   **Output:** Text message to be displayed by the UI/UX Widget Module.

### 3.7. Adaptive Coaching Module
*   **Responsibilities:**
    *   Learn user's patterns (e.g., common triggers for frustration, typical fatigue onset times).
    *   Adapt feedback messages and suggestions over time to be more personalized and effective.
*   **Logic:** This is an advanced feature. Initial implementation might involve simple pattern tracking (e.g., what game or situation often precedes high frustration). More complex implementations could involve basic machine learning models trained locally on user data.
*   **Data Interaction:** Reads from and writes to Local Data Storage Module (e.g., user patterns, message effectiveness).
*   **Output:** Modifies the message selection logic in the Feedback & Messaging Module or provides more tailored suggestions.

### 3.8. Reward System Module
*   **Responsibilities:**
    *   Track user's focus consistency and other positive metrics.
    *   Unlock achievements or provide positive reinforcement based on predefined goals.
*   **Logic:** Define specific achievements (e.g., "Focused for 30 minutes straight", "Managed frustration successfully 5 times").
*   **Data Interaction:** Reads from and writes to Local Data Storage Module (e.g., achievement progress, unlocked rewards).
*   **Output:** Notifications or visual cues within the UI/UX Widget Module for unlocked achievements.

### 3.9. Local Data Storage Module
*   **Responsibilities:** Store and manage all user-specific data locally.
*   **Data Stored:**
    *   User calibration baselines for metrics.
    *   Historical metric data (optional, for pattern analysis).
    *   Learned patterns for adaptive coaching.
    *   Reward system progress and unlocked achievements.
    *   User preferences (widget position, transparency, etc.).
*   **Technology:** Lightweight local database (e.g., SQLite) or structured files (e.g., JSON, CSV).

### 3.10. Configuration Module
*   **Responsibilities:**
    *   Allow users to initiate calibration for metrics.
    *   Customize widget appearance (position, size, transparency).
    *   Manage data privacy settings (e.g., data retention period for historical metrics).
    *   Enable/disable certain features (e.g., adaptive coaching, reward system).
*   **Interface:** A simple settings panel accessible through the widget or a system tray icon.

## 4. Data Flow Example (Single Cycle)

1.  **Input Module** captures a frame from the webcam.
2.  **CV Module** processes the frame: detects face, extracts landmarks, estimates pose, analyzes expressions/emotions.
3.  **Metric Calculation Module** uses CV data to compute Attention, Fatigue, Frustration, Engagement, and Distraction percentages.
4.  **State Classification Module** determines the user's current state based on these metrics and thresholds.
5.  **Adaptive Coaching Module** (if active) analyzes current state and historical patterns to potentially refine feedback strategy.
6.  **Reward System Module** (if active) checks if current state/metrics contribute to any achievements.
7.  **Feedback & Messaging Module** selects an appropriate message based on the classified state (and input from Adaptive Coaching).
8.  **UI/UX Widget Module** updates the displayed metric bars and shows the selected message.
9.  Relevant data (metrics, state changes, achievement progress) is logged by the **Local Data Storage Module**.

This cycle repeats every few seconds.

## 5. Technology Stack Summary (Initial Proposal)

*   **Core Language:** Python 3.x
*   **Webcam Access:** OpenCV
*   **Face/Landmark/Expression Detection:** MediaPipe
*   **Emotion Classification:** DeepFace (with a lightweight model), potentially with future fine-tuning.
*   **UI/UX Overlay:** Tkinter, PyQt, or Kivy (to be finalized based on overlay requirements and ease of use).
*   **Local Data Storage:** SQLite or JSON files.

This architecture provides a modular and scalable foundation for the GameBuddy Focus Tracker, addressing the core requirements while allowing for future expansion of features.
