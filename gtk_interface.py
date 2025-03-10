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

class ThermalView(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.current_frame = None
        self.frame_count = 0
        self.set_size_request(384, 288)
        self.set_vexpand(True)
        self.set_hexpand(True)
        # Set the draw function for the drawing area
        self.set_draw_func(self.on_draw)
        print("ThermalView initialized")  # Debug print
        
    def update_frame(self, frame):
        print(f"ThermalView update_frame called with frame shape: {frame.shape}")  # Debug print
        self.current_frame = frame
        self.frame_count += 1
        self.queue_draw()  # Request a redraw
        print(f"Frame {self.frame_count} update requested")  # Debug print
        
    def on_draw(self, widget, cr, width, height):
        print("ThermalView on_draw called")  # Debug print
        if self.current_frame is None:
            print("Current frame is None")  # Debug print
            # Draw "Waiting for camera" text
            cr.set_source_rgb(0, 0, 0)  # Black text
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(20)
            
            # Center the text
            text = "Waiting for camera"
            text_extents = cr.text_extents(text)
            x = (width - text_extents.width) / 2
            y = (height + text_extents.height) / 2
            
            cr.move_to(x, y)
            cr.show_text(text)
            return False
            
        try:
            # Convert BGR to RGB (OpenCV uses BGR)
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            
            # Create a GdkPixbuf from the numpy array
            height, width = frame_rgb.shape[:2]
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                frame_rgb.tobytes(),
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                width,
                height,
                width * 3
            )
            
            # Scale the pixbuf to fit the drawing area
            scale_x = width / pixbuf.get_width()
            scale_y = height / pixbuf.get_height()
            scale = min(scale_x, scale_y)
            
            # Calculate centering offsets
            offset_x = (width - pixbuf.get_width() * scale) / 2
            offset_y = (height - pixbuf.get_height() * scale) / 2
            
            # Draw the pixbuf
            cr.save()
            cr.translate(offset_x, offset_y)
            cr.scale(scale, scale)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
            cr.paint()
            cr.restore()
            
            print(f"Frame {self.frame_count} drawn successfully")  # Debug print
            return True
            
        except Exception as e:
            print(f"Error drawing frame: {e}")  # Debug print
            import traceback
            traceback.print_exc()  # Print full traceback for debugging
            return False

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
            GLib.timeout_add(333, self.update_frame)  # Changed to 33ms for ~30fps
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