import cv2
import numpy as np
import ht301_hacklib

class CameraManager:
    def __init__(self):
        self.cap = None
        # Don't auto-initialize in __init__, let the window control initialization
        
    def initialize(self):
        """Initialize the thermal camera."""
        try:
            self.cap = ht301_hacklib.HT301()
            if self.cap is None:
                print("Camera initialization failed - got None")
                return False
            return True
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            return False
            
    def read_frame(self):
        """Read a frame from the camera and process it."""
        if self.cap is None:
            print("Cannot read frame - camera not initialized")
            return False, None, None
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame from camera")
                return False, None, None
                
            info, lut = self.cap.info()
            frame = frame.astype(np.float32)
            
            # Auto-exposure
            frame -= frame.min()
            frame /= frame.max()
            frame = (np.clip(frame, 0, 1)*255).astype(np.uint8)
            
            return True, frame, info
        except Exception as e:
            print(f"Error reading frame: {e}")
            return False, None, None
            
    def calibrate(self):
        """Calibrate the camera."""
        if self.cap:
            print("Calibrating camera...")
            self.cap.calibrate()
            print("Camera calibration complete")
        else:
            print("Cannot calibrate - camera not initialized")
            
    def release(self):
        """Release the camera resources."""
        if self.cap:
            print("Releasing camera resources...")
            self.cap.release()
            self.cap = None
            print("Camera resources released")
        else:
            print("No camera resources to release") 