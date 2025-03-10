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
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf, Adw

class ThermalView(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.current_frame = None
        self.frame_count = 0
        
        # Create a drawing area for the thermal view
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self.on_draw)
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        
        # Create an overlay to show status text
        self.overlay = Gtk.Overlay()
        self.overlay.set_child(self.drawing_area)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_visible(False)
        self.status_label.add_css_class("status-label")
        self.overlay.add_overlay(self.status_label)
        
        # Add the overlay to the box
        self.append(self.overlay)
        
        # Add CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .status-label {
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
                padding: 8px;
                border-radius: 4px;
                margin: 8px;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def update_frame(self, frame):
        self.current_frame = frame
        self.frame_count += 1
        self.status_label.set_visible(False)
        self.drawing_area.queue_draw()
        
    def on_draw(self, drawing_area, cr, width, height):
        if self.current_frame is None:
            # Show waiting message with proper styling
            self.status_label.set_visible(True)
            self.status_label.set_text("Waiting for camera")
            return False
            
        try:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            
            # Create a GdkPixbuf from the numpy array
            frame_height, frame_width = frame_rgb.shape[:2]
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                frame_rgb.tobytes(),
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                frame_width,
                frame_height,
                frame_width * 3
            )
            
            # Calculate scaling to maintain aspect ratio
            scale_x = width / frame_width
            scale_y = height / frame_height
            scale = min(scale_x, scale_y)
            
            # Calculate centered position
            scaled_width = frame_width * scale
            scaled_height = frame_height * scale
            x_offset = (width - scaled_width) / 2
            y_offset = (height - scaled_height) / 2
            
            # Draw the scaled image
            cr.save()
            cr.translate(x_offset, y_offset)
            cr.scale(scale, scale)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
            cr.get_source().set_filter(cairo.Filter.BILINEAR)
            cr.paint()
            cr.restore()
            
            return True
            
        except Exception as e:
            print(f"Error drawing frame: {e}")
            import traceback
            traceback.print_exc()
            return False

class ThermalCameraWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize camera
        self.cap = None
        self.draw_temp = True
        
        # Create main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create header bar
        header_bar = Adw.HeaderBar()
        self.main_box.append(header_bar)
        
        # Add buttons to header bar
        self.calibrate_button = Gtk.Button(label="Calibrate")
        self.calibrate_button.connect("clicked", self.on_calibrate_clicked)
        header_bar.pack_start(self.calibrate_button)
        
        self.screenshot_button = Gtk.Button(label="Screenshot")
        self.screenshot_button.connect("clicked", self.on_screenshot_clicked)
        header_bar.pack_end(self.screenshot_button)
        
        # Create content area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_vexpand(True)
        content.set_hexpand(True)
        self.main_box.append(content)
        
        # Create breakpoint for responsive layout
        breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 400px"))
        breakpoint.add_setter(content, "orientation", Gtk.Orientation.VERTICAL)
        self.add_breakpoint(breakpoint)
        
        # Create thermal view
        self.thermal_view = ThermalView()
        content.append(self.thermal_view)
        
        # Set window content
        self.set_content(self.main_box)
        
        # Set default window size with minimum constraints
        self.set_default_size(800, 600)
        self.set_size_request(384, 288)  # Minimum size based on thermal camera resolution
        
        # Connect window close signal
        self.connect("close-request", self.on_window_close)
        
        # Connect to realize signal to ensure window is ready
        self.connect("realize", self.on_window_realize)
        
    def on_window_realize(self, window):
        # Initialize camera after window is realized
        GLib.idle_add(self.initialize_camera)
        
    def initialize_camera(self):
        try:
            self.cap = ht301_hacklib.HT301()
            # Start continuous update loop after camera is initialized
            GLib.idle_add(self.update_frame)
            return False
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            self.close()
            return False
        
    def update_frame(self):
        if self.cap is None:
            return True
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                return True
                
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
                
            self.thermal_view.update_frame(frame)
            return True
        except Exception as e:
            print(f"Error updating frame: {e}")
            return True
        
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
        return True

class ThermalCameraApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.thermalcam.app')
        self.window = None
        
    def do_activate(self):
        if not self.window:
            self.window = ThermalCameraWindow(application=self)
            self.window.present()

def main():
    try:
        app = ThermalCameraApp()
        return app.run(None)
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main() 