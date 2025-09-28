from mediapipe.framework.formats import landmark_pb2
import cv2
import mediapipe as mp
import numpy as np
import math
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
# from deepface import DeepFace # Import moved to _load_emotion_model for lazy loading

class CVModule:
    """Processes video frames to extract facial features and emotions with enhanced accuracy."""
    def __init__(self, max_num_faces=1, min_detection_confidence=0.5, min_tracking_confidence=0.5, ear_threshold=0.21, ear_consecutive_frames=2):
        print("Initializing CV Module...")
        # ... (previous __init__ code) ...
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_landmarker.task")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"FaceLandmarker model not found at {model_path}. "
                                    "Please ensure 'face_landmarker.task' is in the same directory as this script.")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=False,
            num_faces=max_num_faces,
            min_face_detection_confidence=min_detection_confidence,
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)

        self.DeepFace = None
        self.emotion_model_loaded = False
        self.ear_threshold = ear_threshold
        self.ear_consecutive_frames_threshold = ear_consecutive_frames
        self.blinking_frames_counter = 0
        self.last_blink_state = False # Though not directly used in blink logic, might be useful elsewhere

        self.model_points_for_pose = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0)
        ], dtype=np.float64)
        self.pose_landmark_indices = [1, 152, 226, 446, 57, 287] # Ensure these are correct!

        self._printed_all_blendshapes_once = False

        # Define landmark indices for specific features for drawing (MediaPipe standard 468/478 landmarks)
        # VERIFY THESE INDICES FOR YOUR SPECIFIC MODEL VERSION (e.g., from MediaPipe documentation)
        self.LIPS_OUTER_INDICES = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146, 61] 
        self.LIPS_INNER_INDICES = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78]
        
        self.LEFT_EYE_OUTLINE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33]
        self.RIGHT_EYE_OUTLINE_INDICES = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466, 263]
        
        # --- ADDED EYEBROW INDICES ---
        # These are based on common MediaPipe FaceMesh 468-landmark models.
        # Adjust if you use a different model or if these don't look right.
        # Order matters for drawing a polyline.
        self.LEFT_EYEBROW_INDICES = [55, 65, 52, 53, 46] # Outer to inner (approx) - not closed
        self.RIGHT_EYEBROW_INDICES = [285, 295, 282, 283, 276] # Outer to inner (approx) - not closed
        # More complete eyebrow (upper and lower contour combined for a filled look, if desired, would be more complex)
        # For a simple line on the upper contour:
        self.LEFT_EYEBROW_UPPER_INDICES = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46] # Left side, medial to lateral
        self.RIGHT_EYEBROW_UPPER_INDICES = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276] # Right side, medial to lateral


        self.LEFT_EYE_EAR_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_EAR_INDICES = [263, 387, 385, 362, 380, 373]

        print("CV Module initialized.")

    # ... (_calculate_ear, _estimate_head_pose, _load_emotion_model, _get_emotions_from_blendshapes, process_frame, _get_empty_cv_output remain the SAME as previous version) ...
    def _calculate_ear(self, eye_landmarks_indices, all_landmarks_2d):
        try:
            max_idx = max(eye_landmarks_indices)
            if max_idx >= len(all_landmarks_2d):
                return 0.3 
            p1 = all_landmarks_2d[eye_landmarks_indices[0]]
            p2 = all_landmarks_2d[eye_landmarks_indices[1]]
            p3 = all_landmarks_2d[eye_landmarks_indices[2]]
            p4 = all_landmarks_2d[eye_landmarks_indices[3]]
            p5 = all_landmarks_2d[eye_landmarks_indices[4]]
            p6 = all_landmarks_2d[eye_landmarks_indices[5]]
            ver_dist1 = np.linalg.norm(p2 - p6)
            ver_dist2 = np.linalg.norm(p3 - p5)
            hor_dist = np.linalg.norm(p1 - p4)
            if hor_dist < 1e-6: 
                return 0.3 
            ear = (ver_dist1 + ver_dist2) / (2.0 * hor_dist)
            return ear
        except IndexError:
            return 0.3 
        except Exception as e:
            return 0.3

    def _estimate_head_pose(self, landmarks_2d_for_pose, image_shape):
        image_height, image_width = image_shape[:2]
        focal_length = image_width 
        camera_center = (image_width / 2, image_height / 2)
        camera_matrix = np.array([
            [focal_length, 0, camera_center[0]],
            [0, focal_length, camera_center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64) 
        pose_data = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0, "rotation_vector": None, "translation_vector": None, "camera_matrix": camera_matrix, "dist_coeffs": dist_coeffs}
        try:
            (success, rvec, tvec) = cv2.solvePnP(
                self.model_points_for_pose, landmarks_2d_for_pose, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )
            if not success: return pose_data
            pose_data["rotation_vector"] = rvec; pose_data["translation_vector"] = tvec
            rotation_matrix, _ = cv2.Rodrigues(rvec)
            sy = math.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] + rotation_matrix[1, 0] * rotation_matrix[1, 0])
            singular = sy < 1e-6
            if not singular:
                pitch = math.atan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
                yaw = math.atan2(-rotation_matrix[2, 0], sy)
                roll = math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
            else:
                pitch = math.atan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
                yaw = math.atan2(-rotation_matrix[2, 0], sy); roll = 0
            pose_data["pitch"] = np.clip(math.degrees(pitch), -60, 60)
            pose_data["yaw"] = np.clip(math.degrees(yaw), -75, 75)
            pose_data["roll"] = np.clip(math.degrees(roll), -45, 45)
            return pose_data
        except cv2.error as e: return pose_data
        except Exception as e: return pose_data
    
    def _load_emotion_model(self):
        if not self.emotion_model_loaded and self.DeepFace is None:
            try:
                from deepface import DeepFace as DFace 
                print("Loading emotion model (DeepFace)... This might take a moment.")
                self.DeepFace = DFace
                dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
                self.DeepFace.analyze(dummy_frame, actions=['emotion'], enforce_detection=False, silent=True)
                self.emotion_model_loaded = True; print("Emotion model (DeepFace) ready.")
            except ImportError:
                print("Warning: DeepFace library not found. Emotion detection will use blendshape fallback.")
                self.emotion_model_loaded = True 
            except Exception as e:
                print(f"Error loading DeepFace model: {e}. Emotion detection will use blendshape fallback.")
                self.emotion_model_loaded = True

    def _get_emotions_from_blendshapes(self, blendshapes):
        bs = blendshapes         
        happy_score = (bs.get("mouthSmileLeft", 0) + bs.get("mouthSmileRight", 0) + bs.get("cheekSquintLeft",0)*0.5 + bs.get("cheekSquintRight",0)*0.5) / 2.5
        sad_score = (bs.get("mouthFrownLeft", 0) + bs.get("mouthFrownRight", 0) + bs.get("browDownLeft",0)*0.7 + bs.get("browDownRight",0)*0.7 + bs.get("browInnerUp", 0)*0.5 + bs.get("mouthPucker",0)*0.3) / 3.2 
        angry_score = (bs.get("browDownLeft", 0) + bs.get("browDownRight", 0) + bs.get("lipFunnel",0)*0.5 + (bs.get("mouthPressLeft",0) + bs.get("mouthPressRight",0))*0.25 + bs.get("jawForward",0)*0.3 + bs.get("noseSneerLeft",0)*0.2 + bs.get("noseSneerRight",0)*0.2 ) /3.4
        surprise_score = (bs.get("eyeWideLeft", 0) + bs.get("eyeWideRight", 0) + bs.get("jawOpen", 0)*0.8 + bs.get("browInnerUp",0)*1.2) / 3.0
        neutral_score = bs.get("_neutral", 0.0)
        if not bs or all(v == 0 for v in bs.values()): neutral_score = 0.8 
        total_emotional_score = happy_score + sad_score + angry_score + surprise_score
        if total_emotional_score < 0.1 and neutral_score < 0.5: neutral_score = min(1.0, neutral_score + 0.3)
        emotions = {"happy": np.clip(happy_score,0,1), "sad": np.clip(sad_score,0,1), "angry": np.clip(angry_score,0,1), "surprise": np.clip(surprise_score,0,1), "neutral": np.clip(neutral_score,0,1), "fear": np.clip((bs.get("eyeWideLeft",0)*0.6 + bs.get("eyeWideRight",0)*0.6 + bs.get("mouthStretchLeft",0)*0.4 + bs.get("mouthStretchRight",0)*0.4 + bs.get("browInnerUp",0)*0.5)/2.5,0,1), "disgust": np.clip((bs.get("noseSneerLeft",0) + bs.get("noseSneerRight",0) + bs.get("mouthShrugUpper",0)*0.5)/2.5,0,1)}
        return emotions

    def process_frame(self, frame: np.ndarray):
        if frame is None or frame.size == 0: return self._get_empty_cv_output()
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            detection_result = self.face_landmarker.detect(mp_image)
        except Exception as e: return self._get_empty_cv_output()
        cv_output = self._get_empty_cv_output() 
        if detection_result and detection_result.face_landmarks:
            cv_output["face_detected"] = True; face_landmarks_mp = detection_result.face_landmarks[0] 
            image_rows, image_cols = frame.shape[:2]; landmarks_2d_list, landmarks_3d_list, x_coords, y_coords = [], [], [], []
            for idx, lm in enumerate(face_landmarks_mp):
                cx, cy = int(lm.x * image_cols), int(lm.y * image_rows); landmarks_2d_list.append([cx, cy])
                landmarks_3d_list.append([lm.x, lm.y, lm.z]); x_coords.append(cx); y_coords.append(cy)
            cv_output["landmarks_2d"] = np.array(landmarks_2d_list, dtype=np.float32)
            cv_output["landmarks_3d"] = np.array(landmarks_3d_list, dtype=np.float32)
            if x_coords and y_coords:
                x_min,x_max=min(x_coords),max(x_coords); y_min,y_max=min(y_coords),max(y_coords)
                cv_output["face_bbox"] = (x_min, y_min, x_max-x_min, y_max-y_min)
            if len(cv_output["landmarks_2d"]) >= max(self.pose_landmark_indices) + 1 :
                landmarks_for_pose_2d_selected = cv_output["landmarks_2d"][self.pose_landmark_indices]
                cv_output["head_pose_data"] = self._estimate_head_pose(landmarks_for_pose_2d_selected, frame.shape)
                cv_output["head_pose"] = {"pitch":cv_output["head_pose_data"]["pitch"], "yaw":cv_output["head_pose_data"]["yaw"], "roll":cv_output["head_pose_data"]["roll"]}
            else:
                cv_output["head_pose_data"] = self._estimate_head_pose(np.zeros((len(self.pose_landmark_indices),2)), frame.shape)
                cv_output["head_pose"] = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
            if detection_result.face_blendshapes:
                blendshapes_mp = detection_result.face_blendshapes[0]
                cv_output["blendshapes"] = {shape.category_name: shape.score for shape in blendshapes_mp}
                if not self._printed_all_blendshapes_once: self._printed_all_blendshapes_once = True
            else: cv_output["blendshapes"] = {} 
            left_eye_indices_mp=self.LEFT_EYE_EAR_INDICES; right_eye_indices_mp=self.RIGHT_EYE_EAR_INDICES
            if len(cv_output["landmarks_2d"]) > max(max(left_eye_indices_mp), max(right_eye_indices_mp)):
                left_ear=self._calculate_ear(left_eye_indices_mp, cv_output["landmarks_2d"])
                right_ear=self._calculate_ear(right_eye_indices_mp, cv_output["landmarks_2d"])
                cv_output["eye_state"]["left_ear"]=left_ear; cv_output["eye_state"]["right_ear"]=right_ear
                avg_ear=(left_ear+right_ear)/2.0; is_currently_closed=avg_ear<self.ear_threshold
                if is_currently_closed: self.blinking_frames_counter += 1
                else:
                    if self.blinking_frames_counter>=self.ear_consecutive_frames_threshold: cv_output["eye_state"]["blinking"] = True 
                    self.blinking_frames_counter = 0 
                self.last_blink_state = cv_output["eye_state"]["blinking"] 
            else:
                cv_output["eye_state"]["left_ear"]=0.3; cv_output["eye_state"]["right_ear"]=0.3
                cv_output["eye_state"]["blinking"]=False; self.blinking_frames_counter = 0
            if not self.emotion_model_loaded: self._load_emotion_model()
            emotions_analyzed_by_deepface = False
            if self.DeepFace and self.emotion_model_loaded : 
                try:
                    x, y, w, h = cv_output["face_bbox"]
                    face_img_for_emotion = frame[max(0,y):y+h, max(0,x):x+w]
                    if face_img_for_emotion.size > 0 and w > 20 and h > 20: 
                        analysis_results = self.DeepFace.analyze(img_path=face_img_for_emotion, actions=['emotion'], enforce_detection=False, silent=True)
                        if isinstance(analysis_results, list): analysis_results = analysis_results[0] 
                        if "emotion" in analysis_results and analysis_results["emotion"]:
                            cv_output["emotion_scores"]=analysis_results["emotion"]; emotions_analyzed_by_deepface = True
                except Exception as e: pass 
            if not emotions_analyzed_by_deepface: cv_output["emotion_scores"] = self._get_emotions_from_blendshapes(cv_output["blendshapes"])
        else: self.blinking_frames_counter=0; self.last_blink_state=False
        if cv_output["blendshapes"] is None: cv_output["blendshapes"] = {}
        if cv_output["emotion_scores"] is None: cv_output["emotion_scores"] = {}
        if "head_pose_data" not in cv_output : cv_output["head_pose_data"] = self._estimate_head_pose(np.zeros((len(self.pose_landmark_indices),2)), frame.shape)
        return cv_output

    def _get_empty_cv_output(self):
        empty_pose_data = self._estimate_head_pose(np.zeros((len(self.pose_landmark_indices),2)), (480,640)) 
        return {"face_detected": False, "landmarks_3d": None, "landmarks_2d": None, "face_bbox": None, "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}, "head_pose_data": empty_pose_data, "eye_state": {"left_ear": 0.3, "right_ear": 0.3, "blinking": False}, "blendshapes": {}, "emotion_scores": self._get_emotions_from_blendshapes({})}


    def draw_landmarks(self, image: np.ndarray, cv_data: dict):
        """Draws detailed landmarks, feature outlines, and head pose information on the image."""
        annotated_image = image.copy()

        if cv_data and cv_data["face_detected"] and cv_data["landmarks_2d"] is not None:
            landmarks = cv_data["landmarks_2d"].astype(int)

            # Helper to draw polylines
            def draw_polyline_from_indices(img, lms, indices, color, thickness=1, is_closed=True):
                # Check if all indices are within the bounds of the landmarks array
                if not all(idx < len(lms) for idx in indices):
                    # print(f"Warning: Landmark index out of bounds for polyline. Max index: {max(indices)}, Landmarks len: {len(lms)}")
                    return # Don't draw if any index is bad
                
                points = np.array([lms[i] for i in indices], dtype=np.int32)
                cv2.polylines(img, [points], is_closed, color, thickness)

            # Draw Eye Outlines
            draw_polyline_from_indices(annotated_image, landmarks, self.LEFT_EYE_OUTLINE_INDICES, (0, 255, 255), 1) # Cyan
            draw_polyline_from_indices(annotated_image, landmarks, self.RIGHT_EYE_OUTLINE_INDICES, (0, 255, 255), 1)

            # Draw EAR points
            for eye_ear_indices_list in [self.LEFT_EYE_EAR_INDICES, self.RIGHT_EYE_EAR_INDICES]:
                for idx in eye_ear_indices_list:
                    if len(landmarks) > idx: cv2.circle(annotated_image, tuple(landmarks[idx]), 2, (255, 100, 0), -1)

            # Draw Lip Outlines
            draw_polyline_from_indices(annotated_image, landmarks, self.LIPS_OUTER_INDICES, (0, 0, 255), 1) # Red
            draw_polyline_from_indices(annotated_image, landmarks, self.LIPS_INNER_INDICES, (50, 50, 150), 1)

            # --- ADDED EYEBROW DRAWING ---
            # Using LEFT_EYEBROW_UPPER_INDICES and RIGHT_EYEBROW_UPPER_INDICES for a single line
            draw_polyline_from_indices(annotated_image, landmarks, self.LEFT_EYEBROW_UPPER_INDICES, (255, 255, 0), 2, is_closed=False) # Yellow, thicker
            draw_polyline_from_indices(annotated_image, landmarks, self.RIGHT_EYEBROW_UPPER_INDICES, (255, 255, 0), 2, is_closed=False)

            # Highlight Head Pose landmarks and draw axes
            # (The rest of draw_landmarks from the previous version remains the same for head pose axes, bbox, and text display)
            if len(landmarks) > max(self.pose_landmark_indices):
                for idx in self.pose_landmark_indices:
                     cv2.circle(annotated_image, tuple(landmarks[idx]), 3, (0, 255, 0), -1) 
                head_pose_data = cv_data.get("head_pose_data")
                if head_pose_data and head_pose_data.get("rotation_vector") is not None:
                    rvec=head_pose_data["rotation_vector"]; tvec=head_pose_data["translation_vector"]
                    cam_matrix=head_pose_data["camera_matrix"]; dist_coeffs_pose=head_pose_data["dist_coeffs"]
                    axis_length = 75 
                    axis_points = np.float32([[axis_length,0,0],[0,axis_length,0],[0,0,axis_length],[0,0,0]]).reshape(-1,3)
                    imgpts, _ = cv2.projectPoints(axis_points, rvec, tvec, cam_matrix, dist_coeffs_pose)
                    imgpts = imgpts.astype(int)
                    origin_point_for_axis = tuple(landmarks[self.pose_landmark_indices[0]]) 
                    cv2.line(annotated_image, origin_point_for_axis, tuple(imgpts[0].ravel()), (0,0,255), 3) 
                    cv2.line(annotated_image, origin_point_for_axis, tuple(imgpts[1].ravel()), (0,255,0), 3) 
                    cv2.line(annotated_image, origin_point_for_axis, tuple(imgpts[2].ravel()), (255,0,0), 3)  

            if cv_data["face_bbox"]:
                x,y,w,h=cv_data["face_bbox"]; cv2.rectangle(annotated_image, (x,y),(x+w,y+h), (200,200,0), 1)
            pose_angles = cv_data["head_pose"]
            cv2.putText(annotated_image,f"P: {pose_angles['pitch']:.1f}",(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            cv2.putText(annotated_image,f"Y: {pose_angles['yaw']:.1f}",(10,60),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            cv2.putText(annotated_image,f"R: {pose_angles['roll']:.1f}",(10,90),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            eye_state=cv_data["eye_state"]
            cv2.putText(annotated_image,f"L EAR: {eye_state['left_ear']:.2f}",(annotated_image.shape[1]-180,30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,255),2)
            cv2.putText(annotated_image,f"R EAR: {eye_state['right_ear']:.2f}",(annotated_image.shape[1]-180,60),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,255),2)
            if eye_state['blinking']: cv2.putText(annotated_image,"BLINK!",(annotated_image.shape[1]-180,90),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,255),2)
            emotions=cv_data.get("emotion_scores")
            if emotions:
                dominant_emotion=max(emotions, key=emotions.get, default="N/A")
                if dominant_emotion != "N/A":
                    score = emotions[dominant_emotion]
                    cv2.putText(annotated_image,f"{dominant_emotion}: {score:.2f}",(10,120),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
            return annotated_image
        else: 
            return image 

    def release(self):
        print("CV Module resources conceptually released (MediaPipe manages its own lifecycle).")


# The __main__ block would be the same as the one from the previous "very detailed" response.
# No changes are needed in __main__ to see the eyebrow drawing, as it's handled by the updated draw_landmarks.
if __name__ == "__main__":
    print("Testing CV Module with enhanced features & drawing (including eyebrows)...")

    input_module_available = False
    input_src = None 
    try:
        from input_module import InputModule 
        input_module_available = True
    except ImportError:
        print("InputModule not available. CV Module test will not use live camera feed.")
        InputModule = None 
    cv_mod = CVModule()

    if InputModule and input_module_available:
        try:
            input_src = InputModule(source_id=0) 
            print("Attempting to get first frame from InputModule to check camera/source...")
            first_frame_test = input_src.get_frame()
            if first_frame_test is None:
                print("Failed to get initial frame from InputModule. Camera might not be working, source unavailable, or end of file.")
                if hasattr(input_src, 'release'): input_src.release()
                input_src = None 
            else:
                print("InputModule successfully provided an initial frame. Proceeding with live test.")
        except Exception as e:
            print(f"Error initializing or getting first frame from InputModule: {e}")
            if input_src and hasattr(input_src, 'release'):
                input_src.release()
            input_src = None

    if input_src: 
            print("\n--- Live Feed Test ---")
            print("Press 'q' to quit the live feed test.")
            frame_count = 0
            max_frames_live_test = 1000 # Increased for more viewing time
            current_frame = first_frame_test 
            while frame_count < max_frames_live_test:
                if current_frame is None and frame_count > 0: 
                    print(f"Frame {frame_count}: End of video stream or error from InputModule.")
                    break
                if current_frame is None and frame_count == 0: 
                     break 
                cv_data = cv_mod.process_frame(current_frame.copy()) 
                
                if frame_count % 30 == 0: # Print summary every second approx
                    print(f"\n--- Frame {frame_count} (Live Summary) ---")
                    if cv_data["face_detected"]:
                        eye_state = cv_data['eye_state']; head_pose = cv_data['head_pose']; emotions = cv_data['emotion_scores']
                        print(f"  Head Pose: P={head_pose['pitch']:.1f}, Y={head_pose['yaw']:.1f}, R={head_pose['roll']:.1f}")
                        print(f"  Eye State: EAR L={eye_state['left_ear']:.3f}, R={eye_state['right_ear']:.3f}, Blink={eye_state['blinking']}")
                        if emotions: print(f"  Emotion (Dom): {max(emotions, key=emotions.get, default='N/A')}={emotions.get(max(emotions, key=emotions.get, default='N/A'),0):.2f}")
                    else: print(f"  No face detected.")

                annotated_frame = cv_mod.draw_landmarks(current_frame, cv_data) 
                cv2.imshow("CV Module Live Test", annotated_frame)
                
                frame_count += 1
                if cv2.waitKey(5) & 0xFF == ord('q'): break
                if frame_count < max_frames_live_test : current_frame = input_src.get_frame()
            
            if hasattr(input_src, 'release'): input_src.release()
            cv2.destroyWindow("CV Module Live Test") 
    else:
        print("\n--- Live Feed Test Skipped ---")

    print("\n--- Static Image Test ---")
    dummy_frame_path = "test_face_image.jpg" 
    if os.path.exists(dummy_frame_path):
        dummy_frame = cv2.imread(dummy_frame_path)
        if dummy_frame is None:
            print(f"Error: Failed to load image at {dummy_frame_path}. Using black fallback.")
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8) 
        else: print(f"Loaded test image: {dummy_frame_path}")
    else:
        print(f"Test image '{dummy_frame_path}' not found. Using a black dummy frame.")
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    if dummy_frame.size > 0:
        print("Processing static frame...")
        cv_data_static = cv_mod.process_frame(dummy_frame.copy())
        print("\n--- Static Frame Results (Console Summary) ---")
        if cv_data_static["face_detected"]:
            eye_state_s=cv_data_static['eye_state']; head_pose_s=cv_data_static['head_pose']; emotions_s=cv_data_static['emotion_scores']
            print(f"  Head Pose: P={head_pose_s['pitch']:.1f}, Y={head_pose_s['yaw']:.1f}, R={head_pose_s['roll']:.1f}")
            print(f"  Eye State: L_EAR={eye_state_s['left_ear']:.3f},R_EAR={eye_state_s['right_ear']:.3f},Blink={eye_state_s['blinking']}")
            if emotions_s: print(f"  Emotion(Dom): {max(emotions_s, key=emotions_s.get, default='N/A')}={emotions_s.get(max(emotions_s, key=emotions_s.get, default='N/A'),0):.2f}")
        else: print("  No Face Detected in the static image.")

        annotated_dummy_frame = cv_mod.draw_landmarks(dummy_frame, cv_data_static)
        cv2.imshow("CV Module Static Test", annotated_dummy_frame)
        print("\nShowing static test image result. Press any key to close this window.")
        cv2.waitKey(0)
        cv2.destroyWindow("CV Module Static Test")
    else:
        print("Failed to create or load a valid dummy static frame for testing.")
    cv_mod.release()
    cv2.destroyAllWindows() 
    print("\nCV Module detailed test finished.")