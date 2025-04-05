import cv2
import time
import os
import numpy as np
from .utils import get_videos_dir

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.is_raw_recording = False
        self.video_writer = None
        self.raw_file = None
        self.recording_start_time = None
        self.raw_recording_start_time = None
        
    def start_recording(self, frame):
        """Start recording video with frame dimensions."""
        if frame is None:
            print("Error: No frame available to start recording")
            return False
            
        try:
            # Setup video recording
            height, width = frame.shape[:2]
            base_filename = time.strftime("%Y-%m-%d_%H:%M:%S")
            video_path = os.path.join(get_videos_dir(), base_filename + '.mp4')
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            self.video_writer = cv2.VideoWriter(video_path, fourcc, 25.0, (width, height))
            
            self.recording_start_time = time.time()
            self.is_recording = True
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.cleanup()
            return False
            
    def start_raw_recording(self, frame_raw):
        """Start recording raw data."""
        if frame_raw is None:
            print("Error: No raw frame available to start recording")
            return False
            
        try:
            base_filename = time.strftime("%Y-%m-%d_%H:%M:%S")
            raw_path = os.path.join(get_videos_dir(), base_filename + '.raw')
            
            # Initialize raw data file
            self.raw_file = open(raw_path, 'wb')
            # Write header with frame dimensions and data type
            header = np.array([frame_raw.shape[0], frame_raw.shape[1], frame_raw.dtype.itemsize], dtype=np.int32)
            header.tofile(self.raw_file)
            
            self.raw_recording_start_time = time.time()
            self.is_raw_recording = True
            return True
        except Exception as e:
            print(f"Error starting raw recording: {e}")
            self.cleanup_raw()
            return False
            
    def stop_recording(self):
        """Stop video recording and release resources."""
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        self.recording_start_time = None
            
    def stop_raw_recording(self):
        """Stop raw recording and release resources."""
        self.is_raw_recording = False
        if self.raw_file is not None:
            self.raw_file.close()
            self.raw_file = None
        self.raw_recording_start_time = None
            
    def write_frame(self, frame):
        """Write a frame to video if recording."""
        if not self.is_recording:
            return False
            
        try:
            # Write processed frame to video
            if self.video_writer is not None and frame is not None:
                self.video_writer.write(frame)
            return True
        except Exception as e:
            print(f"Error writing frame: {e}")
            return False
            
    def write_raw_frame(self, frame_raw):
        """Write raw frame data if raw recording."""
        if not self.is_raw_recording:
            return False
            
        try:
            # Write raw frame data
            if self.raw_file is not None and frame_raw is not None:
                frame_raw.tofile(self.raw_file)
            return True
        except Exception as e:
            print(f"Error writing raw frame: {e}")
            return False
        
    def cleanup(self):
        """Clean up all resources."""
        self.stop_recording()
        self.stop_raw_recording()
        
    def cleanup_raw(self):
        """Clean up raw recording resources."""
        self.stop_raw_recording() 