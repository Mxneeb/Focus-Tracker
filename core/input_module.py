"""Input module for GameBuddy Focus Tracker.
Handles webcam access and frame retrieval.
"""

import cv2

class InputModule:
    """Handles capturing video frames from a webcam."""
    def __init__(self, source_id=0):
        """Initialize the webcam.

        Args:
            source_id (int): The ID of the camera source (default is 0).
        """
        self.source_id = source_id
        self.cap = None
        self._initialize_capture()

    def _initialize_capture(self):
        """Initializes the VideoCapture object."""
        try:
            self.cap = cv2.VideoCapture(self.source_id)
            if not self.cap.isOpened():
                print(f"Error: Could not open video source {self.source_id}")
                self.cap = None # Ensure cap is None if not opened
            else:
                print(f"Successfully opened video source {self.source_id}")
        except Exception as e:
            print(f"Exception while initializing video capture: {e}")
            self.cap = None

    def get_frame(self):
        """Retrieves a single frame from the webcam.

        Returns:
            numpy.ndarray: The captured frame, or None if an error occurs or capture is not initialized.
        """
        if self.cap is None or not self.cap.isOpened():
            # print("Capture device not ready or not opened.")
            # Try to reinitialize if it was None (e.g. first call failed)
            if self.cap is None:
                 self._initialize_capture()
                 if self.cap is None: # Still None after re-attempt
                     return None
            else: # Not opened but not None (should not happen if _initialize_capture sets to None on fail)
                 return None
        
        ret, frame = self.cap.read()
        if not ret:
            # print("Error: Could not read frame from video source.")
            return None
        return frame

    def release(self):
        """Releases the webcam resource."""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print(f"Released video source {self.source_id}")
        self.cap = None

if __name__ == "__main__":
    # Test the input module
    print("Testing Input Module...")
    # Attempt to use a common camera ID, then try others if it fails
    test_cam_ids = [0, 1, -1] # -1 can sometimes work for any camera on some systems
    input_src = None

    for cam_id in test_cam_ids:
        print(f"\nAttempting to initialize camera with ID: {cam_id}")
        input_src = InputModule(source_id=cam_id)
        if input_src.cap is not None and input_src.cap.isOpened():
            print(f"Successfully initialized camera ID {cam_id}")
            break
        else:
            print(f"Failed to initialize camera ID {cam_id}")
            if input_src:
                input_src.release() # Clean up if initialized but not opened properly
            input_src = None
    
    if input_src and input_src.cap is not None and input_src.cap.isOpened():
        print("Press 'q' to quit the test window.")
        frame_count = 0
        max_frames_to_test = 100 # Limit test duration

        while frame_count < max_frames_to_test:
            frame = input_src.get_frame()
            if frame is not None:
                cv2.imshow(f"Input Module Test (Cam ID: {input_src.source_id}) - Frame {frame_count + 1}", frame)
                frame_count += 1
            else:
                print("Failed to get frame. Ending test.")
                break

            if cv2.waitKey(20) & 0xFF == ord('q'): # Display each frame for 20ms
                print("Quit key pressed.")
                break
        
        input_src.release()
        cv2.destroyAllWindows()
        print(f"Input module test finished. {frame_count} frames processed.")
    else:
        print("Could not initialize any camera for testing. Please check your camera setup and permissions.")

    print("Input Module test complete.")

