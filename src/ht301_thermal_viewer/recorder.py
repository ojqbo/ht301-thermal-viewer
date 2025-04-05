import cv2
import time
import os
import numpy as np
from .utils import get_videos_dir

class Recorder:
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        self.raw_file = None
        self.recording_start_time = None
        
    def start_recording(self, frame, frame_raw):
        """Start recording video with frame dimensions and raw data."""
        if frame is None or frame_raw is None:
            print("Error: No frame available to start recording")
            return False
            
        try:
            # Setup video recording
            height, width = frame.shape[:2]
            base_filename = time.strftime("%Y-%m-%d_%H:%M:%S")
            video_path = os.path.join(get_videos_dir(), base_filename + '.mp4')
            raw_path = os.path.join(get_videos_dir(), base_filename + '.raw')
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            self.video_writer = cv2.VideoWriter(video_path, fourcc, 25.0, (width, height))
            
            # Initialize raw data file
            self.raw_file = open(raw_path, 'wb')
            # Write header with frame dimensions and data type
            header = np.array([frame_raw.shape[0], frame_raw.shape[1], frame_raw.dtype.itemsize], dtype=np.int32)
            header.tofile(self.raw_file)
            frame_raw.tofile(self.raw_file)

            self.recording_start_time = time.time()
            self.is_recording = True
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.cleanup()
            return False
            
    def stop_recording(self):
        """Stop recording and release resources."""
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        if self.raw_file is not None:
            self.raw_file.close()
            self.raw_file = None
        self.recording_start_time = None
            
    def write_frame(self, frame, frame_raw):
        """Write a frame to both video and raw data files if recording."""
        if not self.is_recording:
            return False
            
        try:
            # Write processed frame to video
            if self.video_writer is not None and frame is not None:
                self.video_writer.write(frame)
            
            # Write raw frame data
            if self.raw_file is not None and frame_raw is not None:
                frame_raw.tofile(self.raw_file)
            
            return True
        except Exception as e:
            print(f"Error writing frame: {e}")
            return False
        
    def cleanup(self):
        """Clean up resources."""
        self.stop_recording() 