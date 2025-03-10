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

class ShutterButton(Gtk.Button):
    def __init__(self):
        super().__init__()
        
        # Add CSS styling
        self.add_css_class("shutterbutton")
        self.add_css_class("circular")
        self.add_css_class("flat")
        
        # Set up animations
        self.hover_scale = 1.0
        self.press_scale = 1.0
        self.hover_source_id = None
        self.press_source_id = None
        self.hover_target = 1.0
        self.press_target = 1.0
        
        # Set up drawing area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_content_width(48)
        self.drawing_area.set_content_height(48)
        self.drawing_area.set_draw_func(self.on_draw)
        self.set_child(self.drawing_area)
        
        # Add hover controller
        hover = Gtk.EventControllerMotion()
        hover.connect("enter", self.on_hover_enter)
        hover.connect("leave", self.on_hover_leave)
        self.add_controller(hover)
        
        # Add click controller
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_press)
        click.connect("released", self.on_release)
        self.add_controller(click)
        
        # Add CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .shutterbutton {
                margin: 12px;
                padding: 0;
                min-width: 48px;
                min-height: 48px;
            }
            .shutterbutton.circular {
                border-radius: 9999px;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def start_animation(self, is_hover, target):
        """Start a new animation (hover or press)"""
        if is_hover:
            if self.hover_source_id is not None:
                GLib.source_remove(self.hover_source_id)
                self.hover_source_id = None
            self.hover_target = target
        else:
            if self.press_source_id is not None:
                GLib.source_remove(self.press_source_id)
                self.press_source_id = None
            self.press_target = target
            
        def update_animation(is_hover):
            if is_hover:
                current = self.hover_scale
                target = self.hover_target
                step = 0.05
            else:
                current = self.press_scale
                target = self.press_target
                step = 0.1
                
            # Calculate new value
            if current < target:
                new_value = min(current + step, target)
            else:
                new_value = max(current - step, target)
                
            # Update the scale
            if is_hover:
                self.hover_scale = new_value
            else:
                self.press_scale = new_value
                
            # Queue redraw
            self.drawing_area.queue_draw()
            
            # Continue if not at target
            if abs(new_value - target) > 0.001:
                return True
                
            # Clear source ID since we're done
            if is_hover:
                self.hover_source_id = None
            else:
                self.press_source_id = None
            return False
            
        # Start the animation
        if is_hover:
            self.hover_source_id = GLib.timeout_add(16, update_animation, True)
        else:
            self.press_source_id = GLib.timeout_add(16, update_animation, False)
        
    def on_draw(self, drawing_area, cr, width, height):
        # Calculate sizes
        size = min(width, height)
        border_width = size / 8.0
        center_x = width / 2
        center_y = height / 2
        radius = (size - border_width * 2) / 2
        
        # Apply scaling
        cr.save()
        cr.translate(center_x, center_y)
        scale = self.hover_scale * self.press_scale
        cr.scale(scale, scale)
        cr.translate(-center_x, -center_y)
        
        # Draw outer circle
        cr.arc(center_x, center_y, radius + border_width/2, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(border_width)
        cr.stroke()
        
        # Draw inner circle
        cr.arc(center_x, center_y, radius - border_width/2, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
        cr.restore()
        return True
        
    def on_hover_enter(self, controller, x, y):
        self.start_animation(True, 1.05)  # Scale up to 105%
        
    def on_hover_leave(self, controller):
        self.start_animation(True, 1.0)  # Scale back to 100%
        
    def on_press(self, gesture, n_press, x, y):
        self.start_animation(False, 0.9)  # Scale down to 90%
        
    def on_release(self, gesture, n_press, x, y):
        self.start_animation(False, 1.0)  # Scale back to 100%

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
        
        # Create controls box
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        controls.set_halign(Gtk.Align.CENTER)
        controls.add_css_class("controls")
        content.append(controls)
        
        # Add shutter button
        self.shutter_button = ShutterButton()
        self.shutter_button.connect("clicked", self.on_screenshot_clicked)
        controls.append(self.shutter_button)
        
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