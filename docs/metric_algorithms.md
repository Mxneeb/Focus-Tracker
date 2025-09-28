# GameBuddy Focus Tracker: Metric Algorithms and State Classification Logic

## 1. Introduction

This document outlines the algorithms for calculating the five key gamer metrics (Attention, Fatigue, Frustration, Engagement, Distraction) and the logic for classifying the user's overall state. These calculations will primarily use data extracted by the Computer Vision (CV) Module, including facial landmarks, head pose, eye state, and emotion/expression scores.

## 2. General Principles for Metric Calculation

*   **Normalization:** All metrics will be normalized to a percentage range of 0-100% for easy interpretation and display.
*   **Smoothing:** Raw metric values will be smoothed over a short time window (e.g., using a rolling average of the last N seconds of data) to prevent jittery or overly sensitive outputs.
*   **Input Data:** Derived from the CV Module (e.g., MediaPipe for landmarks/blendshapes, DeepFace for emotion scores).
*   **User Calibration (Optional but Recommended):** For several metrics, an optional calibration step will allow the system to learn the user's baseline facial behaviors (e.g., neutral head pose, typical blink rate, baseline expression during focus). This helps personalize the metric calculations.
*   **Weights and Thresholds:** The specific weights (w_i) and penalty factors (p_i) in the formulas below are indicative and will require tuning and experimentation during development. Thresholds for state classification will also be tuned.

## 3. Metric Calculation Algorithms

### 3.1. Attention Level (%)

*   **Concept:** Measures how well the user keeps their eyes and focus on the screen/game.
*   **Inputs from CV Module:**
    *   `GazeFocusScore`: Estimated by eye landmarks (pupil position relative to eye corners) and head pose (yaw, pitch). Assumes the screen is directly in front. Score is higher when gaze and head are directed towards the screen.
    *   `TimeOnScreenScore`: Percentage of time over the last N seconds that gaze is directed towards the screen.
    *   `HeadPoseScore`: Score based on deviation from a forward-facing head pose (calibrated or assumed). Lower score for significant deviations.
    *   `FacialEngagementScore_Att`: Score based on positive facial expressions indicative of engagement (e.g., slight smile, focused brow, from MediaPipe blendshapes or DeepFace "happy" score, specifically tuned for attention context).
    *   `BlinkPenalty`: Penalty applied if blink rate significantly exceeds a calibrated baseline (could indicate distraction or restlessness, distinct from fatigue-related blinks).
    *   `DistractionEventPenalty`: Penalty for sustained gaze aversion or head turns away from the screen.
*   **Formula Sketch:**
    `Attention_Raw = (w_att1 * GazeFocusScore) + (w_att2 * TimeOnScreenScore) + (w_att3 * HeadPoseScore) + (w_att4 * FacialEngagementScore_Att) - (p_att1 * BlinkPenalty) - (p_att2 * DistractionEventPenalty)`
    `Attention_Level = normalize(smooth(Attention_Raw), 0, 100)`
*   **Calibration:** User performs a short "focused gaming" session. The system records baseline gaze direction, head pose, and blink rate during this period.

### 3.2. Fatigue Level (%)

*   **Concept:** Measures signs of tiredness.
*   **Inputs from CV Module:**
    *   `YawnScore`: Frequency and/or duration of detected yawns (using mouth landmarks and MediaPipe blendshapes for mouth opening and shape).
    *   `PERCLOS_Score`: PERcentage of Eye CLOsure over a time window (e.g., last 60 seconds). Calculated from eye landmark data indicating eye openness.
    *   `ProlongedEyeClosureScore`: Score based on the frequency and duration of eye closures significantly longer than normal blinks.
    *   `HeadDroopScore`: Score based on downward head pitch angle changes indicative of drowsiness.
    *   `ReducedBlinkRateScore`: Significantly lower blink rate than baseline can sometimes indicate drowsiness/staring.
*   **Formula Sketch:**
    `Fatigue_Raw = (w_fat1 * YawnScore) + (w_fat2 * PERCLOS_Score) + (w_fat3 * ProlongedEyeClosureScore) + (w_fat4 * HeadDroopScore) + (w_fat5 * ReducedBlinkRateScore)`
    `Fatigue_Level = normalize(smooth(Fatigue_Raw), 0, 100)`
*   **Calibration:** Establish baseline PERCLOS, blink rate, and head posture during a non-fatigued state.

### 3.3. Frustration Level (%)

*   **Concept:** Measures signs of frustration, anger, or negative stress.
*   **Inputs from CV Module:**
    *   `EmotionScore_Frustration`: Direct score for "angry," "sad," or a combined "frustration" class from an emotion recognition model (e.g., DeepFace).
    *   `FrownScore`: Intensity/duration of brow furrowing (from MediaPipe brow landmarks/blendshapes).
    *   `TenseJawScore`: Indicators of jaw clenching or tension (from MediaPipe jaw landmarks/blendshapes).
    *   `LipPressScore`: Intensity/duration of lip compression or pursing (from MediaPipe lip landmarks/blendshapes).
    *   `RapidHeadMovementScore`: Score based on jerky or rapid head movements if correlated with frustration.
*   **Formula Sketch:**
    `Frustration_Raw = (w_frust1 * EmotionScore_Frustration) + (w_frust2 * FrownScore) + (w_frust3 * TenseJawScore) + (w_frust4 * LipPressScore) + (w_frust5 * RapidHeadMovementScore)`
    `Frustration_Level = normalize(smooth(Frustration_Raw), 0, 100)`
*   **Calibration:** Primarily relies on pre-trained emotion models. Fine-tuning with game-specific frustration expressions would be beneficial if data is available.

### 3.4. Engagement Level (%)

*   **Concept:** Measures signs of positive engagement, happiness, or excitement.
*   **Inputs from CV Module:**
    *   `EmotionScore_Engagement`: Direct score for "happy" or "excited" from an emotion recognition model (e.g., DeepFace).
    *   `SmileScore`: Intensity/duration of smiling (from MediaPipe lip corner landmarks/blendshapes).
    *   `EyeWideningScore`: Indicators of widened eyes, often associated with excitement or surprise (from MediaPipe eye landmarks/blendshapes).
    *   `PositiveHeadNodScore`: Affirmative head nods if detectable and correlated with engagement.
*   **Formula Sketch:**
    `Engagement_Raw = (w_eng1 * EmotionScore_Engagement) + (w_eng2 * SmileScore) + (w_eng3 * EyeWideningScore) + (w_eng4 * PositiveHeadNodScore)`
    `Engagement_Level = normalize(smooth(Engagement_Raw), 0, 100)`
*   **Calibration:** Observe user during known positive/engaging gameplay moments to fine-tune expression mapping.

### 3.5. Distraction Level (%)

*   **Concept:** Measures how frequently the user looks away or shows signs of not paying attention to the game.
*   **Inputs from CV Module:**
    *   `GazeAversionScore`: Frequency and duration of gaze directed significantly away from the assumed screen position.
    *   `HeadTurnScore`: Frequency and duration of significant head yaw/pitch changes away from the screen.
    *   `ExcessiveBlinkRateScore_Distraction`: Blink rate significantly above baseline that isn't attributed to fatigue (can indicate restlessness or scanning the environment).
*   **Formula Sketch:**
    `Distraction_Raw = (w_dist1 * GazeAversionScore) + (w_dist2 * HeadTurnScore) + (w_dist3 * ExcessiveBlinkRateScore_Distraction)`
    `Distraction_Level = normalize(smooth(Distraction_Raw), 0, 100)`
    Alternatively, Distraction can be inversely related to Attention: `Distraction_Level = 100 - Attention_Level` if Attention already captures these elements well.
*   **Calibration:** Baseline on-screen gaze and head position during focused periods (can use Attention calibration data).

## 4. State Classification Logic

The State Classification Module will use the calculated metric percentages to determine the user's overall state. This involves defining thresholds for each metric. The following are example states and potential trigger conditions. These will be refined during development.

*   **State: "Highly Focused & Engaged"**
    *   Conditions: Attention > 85% AND Engagement > 70% AND Frustration < 25% AND Fatigue < 25% AND Distraction < 15%.
    *   Widget Feedback: Green color scheme. Message: "You’re all set and ready to win! Keep that energy up!"

*   **State: "Focused"**
    *   Conditions: Attention > 70% AND Engagement > 50% AND Frustration < 40% AND Fatigue < 40% AND Distraction < 30%.
    *   Widget Feedback: Green/Light Green. Message: "Great focus! Keep it steady."

*   **State: "Slightly Distracted"**
    *   Conditions: Distraction > 30% AND Attention < 70%.
    *   Widget Feedback: Yellow. Message: "Eyes off the prize! Focus up, champion."

*   **State: "Highly Distracted"**
    *   Conditions: Distraction > 60% AND Attention < 50%.
    *   Widget Feedback: Orange/Red. Message: "Losing focus! Try to minimize distractions."

*   **State: "Slightly Fatigued"**
    *   Conditions: Fatigue > 40% AND Fatigue < 70%.
    *   Widget Feedback: Yellow. Message: "Feeling tired? A quick stretch will power you up!"

*   **State: "Highly Fatigued"**
    *   Conditions: Fatigue > 70%.
    *   Widget Feedback: Red. Message: "Fatigue is high. Consider taking a break to refresh!"

*   **State: "Slightly Frustrated"**
    *   Conditions: Frustration > 40% AND Frustration < 70%.
    *   Widget Feedback: Yellow. Message: "Feeling a bit tense? Remember to breathe."

*   **State: "Highly Frustrated"**
    *   Conditions: Frustration > 70%.
    *   Widget Feedback: Red. Message: "Game getting tough? Take a walk outside and return stronger."

*   **State: "Neutral/Calm"**
    *   Conditions: Default state if no other specific states are strongly triggered (e.g., Attention 50-70%, low Frustration, low Fatigue, moderate Engagement).
    *   Widget Feedback: Neutral color (e.g., blue or default). Message: "Stay cool and collected."

### State Prioritization and Cooldown:

*   **Priority:** If multiple state conditions are met, critical states like "Highly Frustrated" or "Highly Fatigued" might take precedence in terms of messaging.
*   **Cooldown:** After a message for a specific state (e.g., "Highly Frustrated") is displayed, a cooldown period (e.g., 1-2 minutes) will prevent the same category of message from being shown too frequently, even if the metric remains high. The visual color cues on the widget will still reflect the current metric levels.
*   **Message Frequency:** Overall message frequency will be kept low to avoid distracting the user, as per user requirements.

This logic will be implemented in the State Classification Module and will drive the Feedback & Messaging Module.
