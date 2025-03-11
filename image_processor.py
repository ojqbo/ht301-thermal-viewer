import cv2
import numpy as np
import utils

class ImageProcessor:
    def __init__(self):
        # Image transformation states
        self.flip_horizontal = False
        self.flip_vertical = False
        self.rotation = 0  # 0, 90, 180, 270 degrees
        self.draw_temp = True
        
        # Initialize colormap settings
        self.colormaps = [
            ('NO_MAP', None),
            ('JET', cv2.COLORMAP_JET),
            ('HOT', cv2.COLORMAP_HOT),
            ('INFERNO', cv2.COLORMAP_INFERNO),
            ('PLASMA', cv2.COLORMAP_PLASMA),
            ('VIRIDIS', cv2.COLORMAP_VIRIDIS),
            ('MAGMA', cv2.COLORMAP_MAGMA),
            ('RAINBOW', cv2.COLORMAP_RAINBOW),
            ('BONE', cv2.COLORMAP_BONE),
        ]
        self.current_colormap_idx = 0
        
    def process_frame(self, frame, info=None):
        """Process a frame with current transformations and colormap."""
        if frame is None:
            return None
            
        # Apply colormap
        if self.colormaps[self.current_colormap_idx][1] is not None:
            frame = cv2.applyColorMap(frame, self.colormaps[self.current_colormap_idx][1])
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
        # Apply transformations
        frame = self.apply_transformations(frame)
        
        # Draw temperature points if enabled and info is provided
        if self.draw_temp and info is not None:
            frame = self.draw_temperature_points(frame, info)
            
        return frame
        
    def apply_transformations(self, frame):
        """Apply current geometric transformations to the frame."""
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)
        if self.flip_vertical:
            frame = cv2.flip(frame, 0)
            
        if self.rotation != 0:
            if self.rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif self.rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
        
    def draw_temperature_points(self, frame, info):
        """Draw temperature points on the frame."""
        # Transform temperature point coordinates based on transformations
        tmin_point = list(info['Tmin_point'])
        tmax_point = list(info['Tmax_point'])
        tcenter_point = list(info['Tcenter_point'])
        
        shape0, shape1 = frame.shape[1], frame.shape[0]
        if self.rotation in [90, 270]:
            shape0, shape1 = shape1, shape0
            
        if self.flip_horizontal:
            tmin_point[0] = shape0 - tmin_point[0]
            tmax_point[0] = shape0 - tmax_point[0]
            tcenter_point[0] = shape0 - tcenter_point[0]
            
        if self.flip_vertical:
            tmin_point[1] = shape1 - tmin_point[1]
            tmax_point[1] = shape1 - tmax_point[1]
            tcenter_point[1] = shape1 - tcenter_point[1]
            
        if self.rotation != 0:
            for point in [tmin_point, tmax_point, tcenter_point]:
                if self.rotation == 90:
                    point[0], point[1] = frame.shape[1] - point[1], point[0]
                elif self.rotation == 180:
                    point[0] = frame.shape[1] - point[0]
                    point[1] = frame.shape[0] - point[1]
                elif self.rotation == 270:
                    point[0], point[1] = point[1], frame.shape[0] - point[0]
                    
        utils.drawTemperature(frame, tuple(tmin_point), info['Tmin_C'], (55,0,0))
        utils.drawTemperature(frame, tuple(tmax_point), info['Tmax_C'], (0,0,85))
        utils.drawTemperature(frame, tuple(tcenter_point), info['Tcenter_C'], (0,255,255))
        
        return frame
        
    def get_current_colormap_name(self):
        """Get the name of the current colormap."""
        return self.colormaps[self.current_colormap_idx][0] 