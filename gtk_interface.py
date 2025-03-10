#!/usr/bin/python3
import numpy as np
import cv2
import math
import ht301_hacklib
import utils
import time
from PIL import Image
import gi
import cairo
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

class ThermalView(Gtk.Picture):
    def __init__(self):
        super().__init__()
        self.current_frame = None
        self.frame_count = 0
        self.set_size_request(384, 288)
        self.set_vexpand(True)
        self.set_hexpand(True)
        print("ThermalView initialized")  # Debug print
        
    def update_frame(self, frame):
        print(f"ThermalView update_frame called with frame shape: {frame.shape}")  # Debug print
        self.current_frame = frame
        self.frame_count += 1
        
        try:
            # Convert BGR to RGB (OpenCV uses BGR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert frame to RGBA format
            frame_height, frame_width = frame_rgb.shape[:2]
            rgba = np.zeros((frame_height, frame_width, 4), dtype=np.uint8)
            rgba[..., :3] = frame_rgb
            rgba[..., 3] = 255
            
            # Create a GdkPixbuf from the numpy array
            # Make sure the data is contiguous in memory
            rgba_contiguous = np.ascontiguousarray(rgba)
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                rgba_contiguous.tobytes(),
                GdkPixbuf.Colorspace.RGB,
                True,  # has_alpha
                8,    # bits_per_sample
                frame_width,
                frame_height,
                frame_width * 4  # rowstride
            )
            
            # Create texture directly from pixbuf
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            
            # Set the texture as the picture source
            self.set_paintable(texture)
            print(f"Frame {self.frame_count} updated successfully")  # Debug print
            
        except Exception as e:
            print(f"Error updating frame: {e}")  # Debug print
            import traceback
            traceback.print_exc()  # Print full traceback for debugging

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
        
        # Create thermal view
        self.thermal_view = ThermalView()
        
        # Create a box to hold the thermal view
        box = Gtk.Box()
        box.set_vexpand(True)
        box.set_hexpand(True)
        box.append(self.thermal_view)
        
        self.set_child(box)
        
        # Set default window size
        self.set_default_size(384, 288)
        
        # Connect window close signal
        self.connect("close-request", self.on_window_close)
        
        # Connect to realize signal to ensure window is ready
        self.connect("realize", self.on_window_realize)
        
        print("ThermalCameraWindow initialized")  # Debug print
        
    def on_window_realize(self, window):
        print("Window realized, initializing camera...")  # Debug print
        # Initialize camera after window is realized
        GLib.idle_add(self.initialize_camera)
        
    def initialize_camera(self):
        print("Initializing camera...")  # Debug print
        try:
            self.cap = ht301_hacklib.HT301()
            # Start update loop after camera is initialized
            GLib.timeout_add(33, self.update_frame)  # Changed to 33ms for ~30fps
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            self.close()
        
    def update_frame(self):
        if self.cap is None:
            print("Camera not initialized, skipping frame update")  # Debug print
            return False
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")  # Debug print
                return False
                
            print(f"Raw frame shape: {frame.shape}, min/max: {frame.min()}/{frame.max()}")  # Debug print
            info, lut = self.cap.info()
            frame = frame.astype(np.float32)
            
            # Auto-exposure
            frame -= frame.min()
            frame /= frame.max()
            frame = (np.clip(frame, 0, 1)*255).astype(np.uint8)
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
            
            print(f"Processed frame shape: {frame.shape}, min/max: {frame.min()}/{frame.max()}")  # Debug print
            
            if self.draw_temp:
                utils.drawTemperature(frame, info['Tmin_point'], info['Tmin_C'], (55,0,0))
                utils.drawTemperature(frame, info['Tmax_point'], info['Tmax_C'], (0,0,85))
                utils.drawTemperature(frame, info['Tcenter_point'], info['Tcenter_C'], (0,255,255))
                
            self.thermal_view.update_frame(frame)
            return True
        except Exception as e:
            print(f"Error updating frame: {e}")
            return False
        
    def on_calibrate_clicked(self, button):
        if self.cap:
            self.cap.calibrate()
                
    def on_screenshot_clicked(self, button):
        if self.thermal_view.current_frame is not None:
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.png'
            cv2.imwrite(filename, self.thermal_view.current_frame)
            
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
    print("Starting Thermal Camera Application...")  # Debug print
    try:
        app = ThermalCameraApp()
        print("Application created, running main loop...")  # Debug print
        return app.run(None)
    except Exception as e:
        print(f"Error starting application: {e}")  # Debug print
        return 1

if __name__ == '__main__':
    print("Script started")  # Debug print
    exit_code = main()
    print(f"Application exited with code: {exit_code}")  # Debug print 