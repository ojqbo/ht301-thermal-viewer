#!/usr/bin/python3
import numpy as np
import cv2
import math
import ht301_hacklib
import utils
import time
from PIL import Image
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk

class ThermalCameraWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize camera
        self.cap = None
        self.draw_temp = True
        
        # Create header bar
        header_bar = Gtk.HeaderBar()
        self.set_titlebar(header_bar)
        
        # Add buttons to header bar
        self.calibrate_button = Gtk.Button(label="Calibrate")
        self.calibrate_button.connect("clicked", self.on_calibrate_clicked)
        header_bar.pack_start(self.calibrate_button)
        
        self.screenshot_button = Gtk.Button(label="Screenshot")
        self.screenshot_button.connect("clicked", self.on_screenshot_clicked)
        header_bar.pack_end(self.screenshot_button)
        
        # Create drawing area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(384, 288)  # Set minimum size
        self.drawing_area.set_draw_func(self.on_draw, None)
        self.set_child(self.drawing_area)
        
        # Set default window size
        self.set_default_size(384, 288)
        
        # Connect window close signal
        self.connect("close-request", self.on_window_close)
        
        # Initialize camera after window is created
        GLib.idle_add(self.initialize_camera)
        
    def initialize_camera(self):
        try:
            self.cap = ht301_hacklib.HT301()
            # Start update loop after camera is initialized
            GLib.timeout_add(.033, self.update_frame)
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            self.close()
        
    def on_draw(self, drawing_area, cairo, width, height, user_data):
        if not hasattr(self, 'current_frame'):
            return
            
        # Get the frame dimensions
        frame_height, frame_width = self.current_frame.shape[:2]
        
        # Calculate scaling to fit the drawing area
        scale_x = width / frame_width
        scale_y = height / frame_height
        scale = min(scale_x, scale_y)
        
        # Calculate centering offsets
        offset_x = (width - frame_width * scale) / 2
        offset_y = (height - frame_height * scale) / 2
        
        # Create a new surface for the frame
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, frame_width, frame_height)
        ctx = cairo.Context(surface)
        
        # Draw the frame data
        for y in range(frame_height):
            for x in range(frame_width):
                b, g, r = self.current_frame[y, x]
                ctx.set_source_rgb(r/255.0, g/255.0, b/255.0)
                ctx.rectangle(x, y, 1, 1)
                ctx.fill()
        
        # Draw the surface with scaling and centering
        cairo.save()
        cairo.translate(offset_x, offset_y)
        cairo.scale(scale, scale)
        cairo.set_source_surface(surface, 0, 0)
        cairo.paint()
        cairo.restore()
        
    def update_frame(self):
        if self.cap is None:
            return False
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                return False
                
            info, lut = self.cap.info()
            frame = frame.astype(np.float32)
            
            # Auto-exposure
            frame -= frame.min()
            frame /= frame.max()
            frame = (np.clip(frame, 0, 1)*255).astype(np.uint8)
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
            
            if self.draw_temp:
                utils.drawTemperature(frame, info['Tmin_point'], info['Tmin_C'], (55,0,0))
                utils.drawTemperature(frame, info['Tmax_point'], info['Tmax_C'], (0,0,85))
                utils.drawTemperature(frame, info['Tcenter_point'], info['Tcenter_C'], (0,255,255))
                
            self.current_frame = frame
            self.drawing_area.queue_draw()
            return True
        except Exception as e:
            print(f"Error updating frame: {e}")
            return False
        
    def on_calibrate_clicked(self, button):
        if self.cap:
            self.cap.calibrate()
        
    def on_screenshot_clicked(self, button):
        if hasattr(self, 'current_frame'):
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.png'
            cv2.imwrite(filename, self.current_frame)
            
    def on_window_close(self, window):
        if self.cap:
            self.cap.release()
        self.get_application().quit()
        return False

class ThermalCameraApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.thermalcam.app')
        self.window = None
        
    def do_activate(self):
        if not self.window:
            self.window = ThermalCameraWindow(title="HT301 Thermal Camera")
            self.window.set_application(self)
            self.window.present()

def main():
    app = ThermalCameraApp()
    return app.run(None)

if __name__ == '__main__':
    main() 