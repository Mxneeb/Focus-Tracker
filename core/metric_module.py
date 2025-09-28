import numpy as np
import time

class MetricModule:
    """Calculates various gamer metrics from CV data."""
    def __init__(self, config=None):
        self.config = config
        self.smoothing_window_size = 3
        self.metric_history = {
            "attention": [], "fatigue": [], "frustration": [], "distraction": []
        }

        # Blink tracking attributes
        self.last_blink_time_for_rate_calc = time.time() # Renamed for clarity
        self.blink_rate_interval = 10 # seconds
        self.blink_count_in_current_interval = 0 # Renamed for clarity
        self.was_blinking_previously = False
        self.current_blink_rate_fatigue_score = 0 # Score derived from blink rate

        # For more nuanced blink analysis (future, if data allows)
        # self.current_blink_start_time = None
        # self.long_blink_threshold = 0.4 # seconds for a 'microsleep' blink
        # self.long_blink_score_component = 0

        print("Metric Module initialized.")

    def _smooth_metric(self, metric_name, current_value):
        # (Same as before)
        history = self.metric_history[metric_name]
        history.append(current_value)
        if len(history) > self.smoothing_window_size:
            history.pop(0)
        return np.mean(history) if history else current_value

    def _normalize_to_percentage(self, value, min_val=0, max_val=1):
        # (Same as before, ensure input value might exceed 1 before clipping)
        normalized_value = max(min_val, min(value, max_val)) # Clip raw value if it goes out of 0-1
        return max(0, min(100, int(normalized_value * 100)))

    def _update_blink_activity(self, eye_state, current_frame_time):
        is_blinking_now = eye_state.get("blinking", False)
        avg_ear = (eye_state.get("left_ear", 0.35) + eye_state.get("right_ear", 0.35)) / 2.0 # Use a higher default if not provided

        # Blink Counting for Rate
        if is_blinking_now and not self.was_blinking_previously:
            self.blink_count_in_current_interval += 1
        self.was_blinking_previously = is_blinking_now

        # Blink Rate Score Calculation
        if current_frame_time - self.last_blink_time_for_rate_calc >= self.blink_rate_interval:
            blinks_per_minute = (self.blink_count_in_current_interval / self.blink_rate_interval) * 60
            # print(f"DEBUG: Blink Rate Calc: {self.blink_count_in_current_interval} blinks in {self.blink_rate_interval}s -> {blinks_per_minute:.1f} BPM")

            if blinks_per_minute <= 18: # Normal
                self.current_blink_rate_fatigue_score = 0.0
            elif blinks_per_minute <= 25: # Slightly elevated
                self.current_blink_rate_fatigue_score = min(1.0, 0.1 + (blinks_per_minute - 18) * 0.05) # 0.1 to 0.45
            elif blinks_per_minute <= 35: # Elevated
                self.current_blink_rate_fatigue_score = min(1.0, 0.45 + (blinks_per_minute - 25) * 0.035) # 0.45 to 0.8
            else: # High
                self.current_blink_rate_fatigue_score = min(1.0, 0.8 + (blinks_per_minute - 35) * 0.04) # 0.8 to 1.0
            # print(f"DEBUG: New Blink Rate Fatigue Score: {self.current_blink_rate_fatigue_score:.2f}")

            self.blink_count_in_current_interval = 0
            self.last_blink_time_for_rate_calc = current_frame_time
        
        # Potential for long blink / microsleep detection (using EAR)
        # This is a simplified PERCLOS variant integrated here for "long blinks"
        long_blink_component = 0.0
        # If eyes are mostly closed (low EAR) for a period.
        # Requires tracking duration of low EAR state across frames.
        # For now, this part is more conceptual as full implementation is complex.
        # What we DO have is instantaneous PERCLOS in calculate_fatigue based on EAR.
        # A true 'long_blink_score' would need state persistence for EAR over time.


    def calculate_attention(self, cv_data):
        if not cv_data or not cv_data.get("face_detected"): return 0

        head_pose = cv_data.get("head_pose", {})
        if not isinstance(head_pose, dict):
            head_pose = {}
        eye_state = cv_data.get("eye_state", {})
        if not isinstance(eye_state, dict):
            eye_state = {}
        blendshapes = cv_data.get("blendshapes", {})
        if not isinstance(blendshapes, dict):
            blendshapes = {}
        emotion_scores = cv_data.get("emotion_scores", {})
        if not isinstance(emotion_scores, dict):
            emotion_scores = {}

        pitch = head_pose.get("pitch", 0); yaw = head_pose.get("yaw", 0)
        head_forward_score = max(0, 1.0 - (abs(pitch) / 45.0) - (abs(yaw) / 45.0)) # Stricter

        avg_ear = (eye_state.get("left_ear", 0.15) + eye_state.get("right_ear", 0.15)) / 2.0 # Default to lower if not present
        eyes_open_score = min(1, avg_ear / 0.28) # Typical open EAR target

        # Eye Gaze Direction (from blendshapes - coarse indication)
        eye_look_penalty = 0.0
        # Using max for out/in as they are opposites on mediapipe
        # If eyeLookOutRight is high, means looking right. If eyeLookOutLeft is high, means looking left.
        # The _Out names are from head's perspective.
        max_eye_look_out = max(blendshapes.get("eyeLookOutRight", 0), blendshapes.get("eyeLookInLeft",0)) # Look Right
        max_eye_look_in = max(blendshapes.get("eyeLookOutLeft",0), blendshapes.get("eyeLookInRight",0)) # Look Left
        max_eye_look_up = max(blendshapes.get("eyeLookUpRight", 0), blendshapes.get("eyeLookUpLeft", 0))
        max_eye_look_down = max(blendshapes.get("eyeLookDownRight", 0), blendshapes.get("eyeLookDownLeft", 0))

        # More than 0.5 on these implies significant eye deviation
        gaze_deviation_threshold = 0.4
        if max_eye_look_out > gaze_deviation_threshold or \
           max_eye_look_in > gaze_deviation_threshold or \
           max_eye_look_up > (gaze_deviation_threshold + 0.1) or \
           max_eye_look_down > (gaze_deviation_threshold + 0.1) : # Stricter for up/down
            eye_look_penalty = 0.4 * max(max_eye_look_out, max_eye_look_in, max_eye_look_up, max_eye_look_down) # Penalize by amount of deviation

        gaze_focus_score = (head_forward_score * 0.5 + eyes_open_score * 0.5) * (1.0 - eye_look_penalty)


        facial_focus_score = emotion_scores.get("neutral", 0.3) * 0.5 + \
                             emotion_scores.get("happy", 0) * 0.2 + \
                             blendshapes.get("mouthClose",0) * 0.3 # Mouth close indicates concentration

        # Penalties
        blink_penalty_val = 0.25 if eye_state.get("blinking", False) else 0
        distraction_event_penalty_val = 0.6 if abs(yaw) > 30 or abs(pitch) > 20 else 0
        # Talking penalty (subtle, uses funnel/pucker which often appear in speech)
        talking_penalty = 0
        if blendshapes.get("mouthFunnel", 0) > 0.3 or blendshapes.get("mouthPucker", 0) > 0.3:
            if blendshapes.get("jawOpen", 0) > 0.1: # Only if mouth is also somewhat open
                talking_penalty = 0.25


        weights = (self.config.get_setting("metrics.attention_weights") if self.config else None) or {
            "gaze_focus": 0.7, "facial_expression": 0.3
        }
        # Compatibility: support old config keys
        if "gaze_focus" not in weights or "facial_expression" not in weights:
            weights = {
                "gaze_focus": weights.get("gaze", 0.4) + weights.get("time_on_screen", 0.3) + weights.get("head_pose", 0.1),
                "facial_expression": weights.get("engagement", 0.2)
            }

        attention_raw = (
            weights["gaze_focus"] * gaze_focus_score +
            weights["facial_expression"] * facial_focus_score -
            blink_penalty_val -
            distraction_event_penalty_val -
            talking_penalty
        )
        attention_raw *= 0.98 # General dampening

        return self._normalize_to_percentage(attention_raw)


    def calculate_fatigue(self, cv_data, current_frame_time_for_debug="N/A"): # Added time for debug print
        if not cv_data or not cv_data.get("face_detected"): return 0

        blendshapes = cv_data.get("blendshapes", {})
        if not isinstance(blendshapes, dict):
            blendshapes = {}
        eye_state = cv_data.get("eye_state", {})
        if not isinstance(eye_state, dict):
            eye_state = {}
        head_pose = cv_data.get("head_pose", {})
        if not isinstance(head_pose, dict):
            head_pose = {}

        # --- Yawn Score ---
        jaw_open = blendshapes.get("jawOpen", 0)
        # DEBUG: Make threshold very low for testing
        yawn_threshold = 0.25 # Lowered from 0.30, was 0.4 previously
        yawn_max_effect = 0.7 # jawOpen value for max yawn score
        yawn_score = 0.0
        if jaw_open > yawn_threshold:
            yawn_score = min(1.0, (jaw_open - yawn_threshold) / (yawn_max_effect - yawn_threshold))
        # print(f"DEBUG Fatigue Frame {current_frame_time_for_debug}: jaw_open={jaw_open:.2f}, yawn_score={yawn_score:.2f} (thresh={yawn_threshold})")


        # --- PERCLOS Score (based on EAR) ---
        avg_ear = (eye_state.get("left_ear", 0.35) + eye_state.get("right_ear", 0.35)) / 2.0 # Default to open if not found
        # DEBUG: Make threshold higher for testing (meaning more sensitive to droopiness)
        perclos_ear_threshold = 0.26 # Raised from 0.25 (was 0.22 way back) means eyes only slightly droopy contribute
        perclos_ear_min_closed = 0.05 # Fully closed
        perclos_score = 0.0
        if avg_ear < perclos_ear_threshold:
            perclos_score = (perclos_ear_threshold - avg_ear) / (perclos_ear_threshold - perclos_ear_min_closed)
            perclos_score = max(0, min(1, perclos_score))
        # print(f"DEBUG Fatigue Frame {current_frame_time_for_debug}: avg_ear={avg_ear:.2f}, perclos_score={perclos_score:.2f} (thresh={perclos_ear_threshold})")

        # --- Head Droop Score ---
        pitch = head_pose.get("pitch", 0)
        # DEBUG: Make threshold very sensitive
        head_droop_threshold = -5 # More sensitive, was -8, was -12
        head_droop_max_effect = -25 # Pitch for max droop score
        head_droop_score = 0.0
        if pitch < head_droop_threshold:
            head_droop_score = abs(pitch - head_droop_threshold) / abs(head_droop_max_effect - head_droop_threshold)
            head_droop_score = max(0, min(1, head_droop_score))
        # print(f"DEBUG Fatigue Frame {current_frame_time_for_debug}: pitch={pitch:.2f}, head_droop_score={head_droop_score:.2f} (thresh={head_droop_threshold})")

        # --- Eye Squint Score ---
        eye_squint_avg = (blendshapes.get("eyeSquintLeft", 0) + blendshapes.get("eyeSquintRight", 0)) / 2.0
        squint_threshold = 0.25 #DEBUG lower this from 0.3 if needed
        eye_squint_score = 0.0
        if eye_squint_avg > squint_threshold:
            eye_squint_score = min(1.0, (eye_squint_avg - squint_threshold) / (0.6 - squint_threshold)) # Max effect at 0.6 squint

        # --- Blink Rate Score (already calculated in _update_blink_activity) ---
        blink_rate_fatigue_score = self.current_blink_rate_fatigue_score # Use the stored value
        # print(f"DEBUG Fatigue Frame {current_frame_time_for_debug}: blink_rate_fatigue_score={blink_rate_fatigue_score:.2f} (from {self.blink_count_in_current_interval} blinks in interval)")


        weights = (self.config.get_setting("metrics.fatigue_weights") if self.config else None) or {
            "yawn": 0.25, "perclos": 0.30, "blink_rate": 0.25, "head_droop": 0.15, "eye_squint": 0.05
        }
        # Compatibility: support old config keys or missing keys
        if any(k not in weights for k in ["yawn", "perclos", "blink_rate", "head_droop", "eye_squint"]):
            weights = {
                "yawn": weights.get("yawn", 0.25),
                "perclos": weights.get("perclos", 0.3),
                "blink_rate": weights.get("blink_rate", 0.25),
                "head_droop": weights.get("head_droop", 0.15),
                "eye_squint": weights.get("eye_squint", 0.05),
                # fallback for old configs
                "eye_closure": weights.get("eye_closure", 0.0)
            }


        fatigue_raw = (
            weights["yawn"] * yawn_score +
            weights["perclos"] * perclos_score +
            weights["blink_rate"] * blink_rate_fatigue_score +
            weights["head_droop"] * head_droop_score +
            weights["eye_squint"] * eye_squint_score
        )
        # print(f"DEBUG Fatigue Frame {current_frame_time_for_debug}: RAW FATIGUE={fatigue_raw:.2f}")
        return self._normalize_to_percentage(fatigue_raw)

    def calculate_frustration(self, cv_data, current_frame_time_for_debug=None):
        blendshapes = cv_data.get("blendshapes", {})
        if not isinstance(blendshapes, dict):
            blendshapes = {}
        # Use only responsive blendshapes
        frown_score = (
            blendshapes.get("browDownLeft", 0) +
            blendshapes.get("browDownRight", 0) +
            blendshapes.get("mouthPressLeft", 0) +
            blendshapes.get("mouthPressRight", 0)
        )
        # Lower threshold for activation
        frustration = frown_score if frown_score > 0.05 else 0.0
        # Optionally add DeepFace emotion score
        emotion_scores = cv_data.get("emotion_scores", {})
        if isinstance(emotion_scores, dict):
            angry_score = emotion_scores.get("angry", 0)
            if angry_score > 1:
                angry_score = angry_score / 100.0
            frustration += angry_score * 0.5
        # Cap at 1.0 for normalization, then scale to 0-100
        frustration = min(frustration, 1.0)
        # Debug: Print top 5 blendshapes
        top_blendshapes = sorted(blendshapes.items(), key=lambda x: -x[1])[:5]
        print(f"Frustration debug: frown_score={frown_score:.2f} angry={emotion_scores.get('angry', 0):.2f} top5={top_blendshapes}")
        return self._normalize_to_percentage(frustration)

    def calculate_distraction(self, cv_data, attention_level):
        if not cv_data or not cv_data.get("face_detected"): return 100
        # Defensive: ensure head_pose is dict if used in future
        head_pose = cv_data.get("head_pose", {})
        if not isinstance(head_pose, dict):
            head_pose = {}
        distraction_level = 100 - attention_level
        return max(0, min(100, int(distraction_level)))

    def calculate_metrics(self, cv_data, current_frame_time_for_sim): # Pass current time for accurate blink update
        if cv_data is None or not cv_data.get("face_detected"):
            self.current_blink_rate_fatigue_score = 0 # Reset if face lost
            return {
                "attention": 0, "fatigue": self.metric_history["fatigue"][-1] if self.metric_history["fatigue"] else 0,
                "frustration": self.metric_history["frustration"][-1] if self.metric_history["frustration"] else 0,
                "distraction": 100
            }

        self._update_blink_activity(cv_data.get("eye_state", {}), current_frame_time_for_sim)

        attention = self.calculate_attention(cv_data)
        fatigue = self.calculate_fatigue(cv_data, current_frame_time_for_debug=f"{current_frame_time_for_sim:.1f}") # Pass time for debug print
        frustration = self.calculate_frustration(cv_data)
        distraction = self.calculate_distraction(cv_data, attention)

        return {
            "attention": self._smooth_metric("attention", attention),
            "fatigue": self._smooth_metric("fatigue", fatigue),
            "frustration": self._smooth_metric("frustration", frustration),
            "distraction": self._smooth_metric("distraction", distraction)
        }

if __name__ == "__main__":
    print("Testing Metric Module with Enhanced Features & Fatigue Debug...")

    class DummyConfig: # (Same as before, but update if new config keys added)
        def get_setting(self, key, default=None): return default

    metric_mod = MetricModule(config=DummyConfig())
    start_sim_time = time.time() # For simulating passage of time in test

    # --- Helper function to create default blendshapes ---
    def get_default_blendshapes():
        return {
            "_neutral": 0.8, "jawOpen": 0.05, "mouthSmileLeft": 0.1, "browDownLeft": 0.05, "browDownRight": 0.05,
            "eyeWideLeft": 0.1, "mouthPressLeft": 0.05, "mouthPressRight": 0.05, "noseSneerLeft": 0.0, "noseSneerRight": 0.0,
            "eyeLookOutRight":0, "eyeLookInLeft":0, "eyeLookOutLeft":0, "eyeLookInRight":0, "eyeLookUpRight":0,
            "eyeLookUpLeft":0, "eyeLookDownRight":0, "eyeLookDownLeft":0, "mouthClose":0.7, "mouthFunnel":0, "mouthPucker":0,
            "eyeSquintLeft":0, "eyeSquintRight":0, "mouthFrownLeft":0, "mouthFrownRight":0, "cheekSquintLeft":0, "cheekSquintRight":0,
            "jawForward":0,
        }
    
    test_cases = [
        {"name": "Neutral/Attentive", "cv_data": {
            "face_detected": True, "head_pose": {"pitch": 0.0, "yaw": 0.0},
            "eye_state": {"left_ear": 0.32, "right_ear": 0.32, "blinking": False},
            "blendshapes": get_default_blendshapes(),
            "emotion_scores": {"neutral": 0.7, "happy": 0.1, "angry": 0.05, "sad": 0.05}
        }},
        {"name": "Slightly Distracted (Eyes Look Right)", "cv_data": {
            "face_detected": True, "head_pose": {"pitch": 5.0, "yaw": 10.0},
            "eye_state": {"left_ear": 0.28, "right_ear": 0.28, "blinking": False},
            "blendshapes": {**get_default_blendshapes(), "eyeLookOutRight": 0.7, "eyeLookInLeft": 0.7}, # Looking hard right
            "emotion_scores": {"neutral": 0.6, "happy": 0.1}
        }},
        # --- FATIGUE TEST CASE --- Focus on this one!
        {"name": "More Fatigued (Droopy, Head, Blinks)", "cv_data": {
            "face_detected": True,
            "head_pose": {"pitch": -7.0, "yaw": 2.0}, # Exceeds head_droop_threshold = -5
            "eye_state": {"left_ear": 0.20, "right_ear": 0.21, "blinking": False}, # avg_ear = 0.205, below perclos_ear_threshold = 0.26
            "blendshapes": {**get_default_blendshapes(),
                            "jawOpen": 0.30, # Exceeds yawn_threshold = 0.25
                            "eyeSquintLeft": 0.3, "eyeSquintRight": 0.3}, # Exceeds squint_threshold = 0.25
            "emotion_scores": {"neutral": 0.4, "sad": 0.2},
            "force_blinks_in_interval": 6 # Simulate 6 blinks in the 10s interval (36 BPM -> should give score)
        }},
        {"name": "Yawning/Very Fatigued (Higher Values)", "cv_data": {
            "face_detected": True, "head_pose": {"pitch": -15.0, "yaw": 5.0},
            "eye_state": {"left_ear": 0.15, "right_ear": 0.15, "blinking": False}, # Avg EAR very low
            "blendshapes": {**get_default_blendshapes(), "jawOpen": 0.6, "eyeSquintLeft": 0.5, "eyeSquintRight": 0.5}, # Strong yawn, squint
            "emotion_scores": {"neutral": 0.2, "sad": 0.3},
            "force_blinks_in_interval": 8 # Higher blink rate
        }},
        {"name": "Frustrated (Multiple Cues)", "cv_data": {
            "face_detected": True, "head_pose": {"pitch": 0.0, "yaw": 0.0},
            "eye_state": {"left_ear": 0.25, "right_ear": 0.25, "blinking": False},
            "blendshapes": {**get_default_blendshapes(),
                            "browDownLeft": 0.7, "browDownRight": 0.7, "mouthPressLeft": 0.5, "mouthPressRight": 0.5,
                            "noseSneerLeft": 0.4, "noseSneerRight": 0.4, "mouthFrownLeft":0.6, "mouthFrownRight":0.6,
                            "cheekSquintLeft": 0.5, "cheekSquintRight":0.5, "jawForward":0.3},
            "emotion_scores": {"neutral": 0.1, "happy": 0.0, "angry": 0.7, "sad": 0.3, "disgust": 0.4}
        }},
        {"name": "No Face", "cv_data": {"face_detected": False}}
    ]

    FRAMES_PER_SECOND_SIM = 30 # How many frames we simulate per second of game time
    SIM_FRAME_DURATION = 1.0 / FRAMES_PER_SECOND_SIM

    for test_idx, test_case in enumerate(test_cases):
        print(f"\n--- Testing Case ({test_idx+1}/{len(test_cases)}): {test_case['name']} ---")
        metric_mod.metric_history = {k: [] for k in metric_mod.metric_history} # Reset history
        metric_mod.blink_count_in_current_interval = 0
        metric_mod.last_blink_time_for_rate_calc = start_sim_time # Reset timer for THIS test case
        metric_mod.was_blinking_previously = False
        metric_mod.current_blink_rate_fatigue_score = 0


        # Simulate for slightly longer than one blink_rate_interval to ensure it fires
        simulation_duration_seconds = metric_mod.blink_rate_interval + 2.0
        num_frames_to_simulate_for_case = int(simulation_duration_seconds * FRAMES_PER_SECOND_SIM)
        
        blinks_to_force = test_case["cv_data"].get("force_blinks_in_interval", 0)
        # Distribute blinks. A blink lasts for ~2-3 frames (0.1s).
        blink_frame_indices = []
        if blinks_to_force > 0:
            # Try to space them somewhat evenly in the first blink_rate_interval
            frames_in_blink_interval = int(metric_mod.blink_rate_interval * FRAMES_PER_SECOND_SIM)
            for k in range(blinks_to_force):
                # Add a blink start index
                blink_start_idx = int((k / blinks_to_force) * frames_in_blink_interval)
                blink_frame_indices.extend([blink_start_idx, blink_start_idx + 1, blink_start_idx + 2]) # Blink lasts 3 frames
        
        print(f"Simulating {num_frames_to_simulate_for_case} frames over {simulation_duration_seconds:.1f}s. Expecting {blinks_to_force} blinks for blink rate. Blink frames: {sorted(list(set(blink_frame_indices))[:10])}...")

        for i in range(num_frames_to_simulate_for_case):
            current_sim_time_in_test = start_sim_time + (i * SIM_FRAME_DURATION)
            cv_input = test_case["cv_data"].copy()
            
            # Update eye_state for blinking based on our schedule
            current_eye_state_sim = cv_input.get("eye_state", {}).copy()
            if i in blink_frame_indices:
                current_eye_state_sim["blinking"] = True
                current_eye_state_sim["left_ear"] = 0.05 # Force EAR low during blink
                current_eye_state_sim["right_ear"] = 0.05
            else:
                # If not a forced blink frame, use original or non-blinking EAR
                original_eye_state = test_case["cv_data"].get("eye_state", {"blinking":False, "left_ear":0.3, "right_ear":0.3})
                current_eye_state_sim["blinking"] = False
                current_eye_state_sim["left_ear"] = original_eye_state.get("left_ear", 0.3)
                current_eye_state_sim["right_ear"] = original_eye_state.get("right_ear", 0.3)

            cv_input["eye_state"] = current_eye_state_sim

            # Make head yaw/pitch vary slightly to test smoothing robustness if desired
            # if 'head_pose' in cv_input:
            #    cv_input['head_pose']['yaw'] += np.sin(i * 0.1) * 2 # Small oscillation

            metrics_dict = metric_mod.calculate_metrics(cv_input, current_sim_time_in_test)
            display_metrics = {k: round(v) for k, v in metrics_dict.items()}
            
            # Print first few, last few, and when blink rate interval might fire
            print_this_frame = False
            if i < 5 or i >= num_frames_to_simulate_for_case - 5:
                print_this_frame = True
            
            # Check if a blink rate calculation was expected around this time
            time_since_last_blink_calc = current_sim_time_in_test - metric_mod.last_blink_time_for_rate_calc
            if metric_mod.blink_rate_interval - 0.2 < time_since_last_blink_calc < metric_mod.blink_rate_interval + 0.2 : # print around interval
                # This logic is tricky due to frame steps vs continuous time
                # A better check might be if `last_blink_time_for_rate_calc` changed in this iteration (AFTER metrics_dict calc)
                 print_this_frame = True


            if print_this_frame or (i % (FRAMES_PER_SECOND_SIM * 2) == 0 and i > 0): # Print every 2 sim seconds
                blinks_done = metric_mod.blink_count_in_current_interval if current_sim_time_in_test - metric_mod.last_blink_time_for_rate_calc < metric_mod.blink_rate_interval else "Calc'd"
                print(f"SimFrame {i+1:3d} (SimTime {current_sim_time_in_test - start_sim_time:.1f}s, BlinksInInt: {blinks_done}): {display_metrics}")
                if test_case['name'].startswith("More Fatigued") or test_case['name'].startswith("Yawning"):
                    pass # Add specific debugs here if needed

    print("\nMetric Module extensive test complete.")