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
from shutter_button import ShutterButton

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
        
        # Create an overlay to show status text and controls
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
        
        # Initialize colormap settings
        self.colormaps = [
            ('JET', cv2.COLORMAP_JET),
            ('HOT', cv2.COLORMAP_HOT),
            ('INFERNO', cv2.COLORMAP_INFERNO),
            ('PLASMA', cv2.COLORMAP_PLASMA),
            ('VIRIDIS', cv2.COLORMAP_VIRIDIS),
            ('MAGMA', cv2.COLORMAP_MAGMA),
            ('RAINBOW', cv2.COLORMAP_RAINBOW),
            ('BONE', cv2.COLORMAP_BONE),
        ]
        self.current_colormap_idx = 0  # Start with JET
        
        # Set window properties
        self.set_default_size(800, 600)
        self.set_size_request(384, 288)  # Minimum size based on thermal camera resolution
        
        # Create main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("main-box")
        
        # Create thermal view
        self.thermal_view = ThermalView()
        self.main_box.append(self.thermal_view)
        
        # Create controls box
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        controls.set_halign(Gtk.Align.CENTER)
        controls.set_valign(Gtk.Align.END)
        controls.set_margin_bottom(16)
        controls.add_css_class("controls")
        controls.add_css_class("controls-container")
        
        # Create top controls box
        top_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        top_controls.set_halign(Gtk.Align.END)
        top_controls.set_valign(Gtk.Align.START)
        top_controls.set_margin_top(16)
        top_controls.set_margin_end(16)
        top_controls.add_css_class("controls")
        top_controls.add_css_class("controls-container")
        
        # Add temperature display toggle button to top controls
        temp_toggle_button = Gtk.ToggleButton()
        temp_toggle_button.set_icon_name("zoom-fit-best-symbolic")  # Changed to crosshair icon
        temp_toggle_button.add_css_class("circular")
        temp_toggle_button.add_css_class("flat")
        temp_toggle_button.add_css_class("temp-toggle-button")
        temp_toggle_button.set_active(self.draw_temp)
        temp_toggle_button.connect("toggled", self.on_temp_toggle)
        temp_toggle_button.set_tooltip_text("Toggle Temperature Display")
        top_controls.append(temp_toggle_button)
        
        # Add colormap toggle button
        colormap_button = Gtk.Button()
        colormap_button.set_icon_name("color-select-symbolic")
        colormap_button.add_css_class("circular")
        colormap_button.add_css_class("flat")
        colormap_button.add_css_class("colormap-button")
        colormap_button.connect("clicked", self.on_colormap_clicked)
        colormap_button.set_tooltip_text(f"Colormap: {self.colormaps[self.current_colormap_idx][0]}")
        top_controls.append(colormap_button)
        
        # Add shutter button
        self.shutter_button = ShutterButton()
        self.shutter_button.connect("clicked", self.on_screenshot_clicked)
        controls.append(self.shutter_button)
        
        # Add calibrate button as a small icon button
        calibrate_button = Gtk.Button()
        calibrate_button.set_icon_name("view-refresh-symbolic")
        calibrate_button.add_css_class("circular")
        calibrate_button.add_css_class("flat")
        calibrate_button.add_css_class("calibrate-button")
        calibrate_button.connect("clicked", self.on_calibrate_clicked)
        calibrate_button.set_tooltip_text("Calibrate")
        controls.append(calibrate_button)
        
        # Add controls to the thermal view's overlay
        self.thermal_view.overlay.add_overlay(controls)
        self.thermal_view.overlay.add_overlay(top_controls)
        
        # Add CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .main-box {
                background-color: black;
            }
            window {
                background-color: black;
            }
            .controls-container {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 9999px;
                padding: 4px;
            }
            .controls button.circular {
                margin: 8px;
                padding: 12px;
                min-width: 48px;
                min-height: 48px;
                border-radius: 9999px;
            }
            .controls button.circular:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            .calibrate-button {
                color: black;
                -gtk-icon-size: 24px;
            }
            .temp-toggle-button {
                color: black;
                -gtk-icon-size: 24px;
            }
            .colormap-button {
                color: black;
                -gtk-icon-size: 24px;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Set window content
        self.set_content(self.main_box)
        
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
            frame = cv2.applyColorMap(frame, self.colormaps[self.current_colormap_idx][1])
            
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
            
    def on_temp_toggle(self, button):
        self.draw_temp = button.get_active()
                
    def on_colormap_clicked(self, button):
        self.current_colormap_idx = (self.current_colormap_idx + 1) % len(self.colormaps)
        button.set_tooltip_text(f"Colormap: {self.colormaps[self.current_colormap_idx][0]}")
                
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