import cv2
import time
import os
from .utils import get_videos_dir

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        
    def start_recording(self, frame):
        """Start recording video with frame dimensions."""
        if frame is None:
            print("Error: No frame available to start recording")
            return False
            
        try:
            height, width = frame.shape[:2]
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.mp4'
            save_path = os.path.join(get_videos_dir(), filename)
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            self.video_writer = cv2.VideoWriter(save_path, fourcc, 25.0, (width, height))
            self.recording_start_time = time.time()
            self.is_recording = True
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False
            
    def stop_recording(self):
        """Stop recording and release resources."""
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            self.recording_start_time = None
            
    def write_frame(self, frame):
        """Write a frame to the video if recording."""
        if self.is_recording and self.video_writer is not None and frame is not None:
            try:
                self.video_writer.write(frame)
                return True
            except Exception as e:
                print(f"Error writing frame: {e}")
                return False
        return False
        
    def cleanup(self):
        """Clean up resources."""
        self.stop_recording() 