import gi
import cv2
import time
import subprocess
import os
from pathlib import Path
from gi.repository import Gtk, GLib, Adw, Gdk, Gio
import numpy as np

from .thermal_view import ThermalView
from .camera_manager import CameraManager
from .image_processor import ImageProcessor
from .recorder import Recorder
from .controls_manager import ControlsManager
from .utils import get_pictures_dir

class ThermalCameraWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set window properties
        self.set_default_size(800, 600)
        # Allow window to scale below native image resolution
        self.set_size_request(350, 300)  # Reasonable minimum size for UI elements
        
        # Initialize components
        self.camera_manager = CameraManager()
        self.image_processor = ImageProcessor()
        self.recorder = Recorder()
        
        # Screen wake lock inhibitor
        self.wake_lock_inhibitor = None
        
        # Auto-rotation lock
        self.original_orientation_lock = None
        
        # Create main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("main-box")
        
        # Create thermal view
        self.thermal_view = ThermalView()
        
        # Enable window dragging from the thermal view area
        drag_gesture = Gtk.GestureDrag.new()
        drag_gesture.set_button(Gdk.BUTTON_PRIMARY)  # Only handle left-click drags
        drag_gesture.connect("drag-begin", self.on_drag_begin)
        drag_gesture.connect("drag-update", self.on_drag_update)
        self.thermal_view.drawing_area.add_controller(drag_gesture)  # Add gesture to drawing area
        
        self.main_box.append(self.thermal_view)
        
        # Create controls
        self.controls_manager = ControlsManager(self, self.image_processor, self.camera_manager, self.recorder)
        self.thermal_view.overlay.add_overlay(self.controls_manager.controls)
        self.thermal_view.overlay.add_overlay(self.controls_manager.top_controls)
        
        # Apply CSS styles
        self.apply_css()
        
        # Set window content
        self.set_content(self.main_box)
        
        # Connect window signals
        self.connect("close-request", self.on_window_close)
        self.connect("realize", self.on_window_realize)
        self.connect("map", self.on_window_map)
        self.connect("unmap", self.on_window_unmap)
        
        # Get the original orientation lock setting
        self.get_original_orientation_lock()
        
    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(str(Path(__file__).parent / "styles.css"))
        
        # Get the default display
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        
    def get_original_orientation_lock(self):
        """Get the original orientation lock setting from gsettings"""
        try:
            result = subprocess.run(
                ['gsettings', 'get', 'org.gnome.settings-daemon.peripherals.touchscreen', 'orientation-lock'],
                capture_output=True,
                text=True,
                check=True
            )
            self.original_orientation_lock = result.stdout.strip()
            print(f"Original orientation lock setting: {self.original_orientation_lock}")
        except Exception as e:
            print(f"Failed to get original orientation lock setting: {e}")
            self.original_orientation_lock = None
        
    def on_window_realize(self, window):
        # Initialize camera after window is realized
        GLib.idle_add(self.initialize_camera)
        
    def on_window_map(self, window):
        # Enable screen wake lock when window is shown
        self.enable_wake_lock()
        # Disable auto-rotation
        self.disable_auto_rotation()
        
    def on_window_unmap(self, window):
        # Disable screen wake lock when window is hidden
        self.disable_wake_lock()
        # Enable auto-rotation
        self.enable_auto_rotation()
        
    def enable_wake_lock(self):
        """Enable screen wake lock to keep the screen on while using the camera"""
        try:
            # Get the application
            app = self.get_application()
            if app:
                # Create a wake lock inhibitor with both SUSPEND and IDLE flags
                # SUSPEND prevents system suspension
                # IDLE prevents the system from going idle
                self.wake_lock_inhibitor = app.inhibit(
                    self,
                    Gtk.ApplicationInhibitFlags.SUSPEND | Gtk.ApplicationInhibitFlags.IDLE,
                    "Thermal Camera Active"
                )
                print("Screen wake lock enabled")
        except Exception as e:
            print(f"Failed to enable screen wake lock: {e}")
            
    def disable_wake_lock(self):
        """Disable screen wake lock"""
        if self.wake_lock_inhibitor:
            try:
                # Get the application
                app = self.get_application()
                if app:
                    app.uninhibit(self.wake_lock_inhibitor)
                    self.wake_lock_inhibitor = None
                    print("Screen wake lock disabled")
            except Exception as e:
                print(f"Failed to disable screen wake lock: {e}")
                
    def disable_auto_rotation(self):
        """Disable auto-rotation using gsettings"""
        try:
            subprocess.run(
                ['gsettings', 'set', 'org.gnome.settings-daemon.peripherals.touchscreen', 'orientation-lock', 'true'],
                check=True
            )
            print("Auto-rotation disabled")
        except Exception as e:
            print(f"Failed to disable auto-rotation: {e}")
            
    def enable_auto_rotation(self):
        """Enable auto-rotation using gsettings"""
        try:
            # Restore the original orientation lock setting
            if self.original_orientation_lock is not None:
                subprocess.run(
                    ['gsettings', 'set', 'org.gnome.settings-daemon.peripherals.touchscreen', 'orientation-lock', self.original_orientation_lock],
                    check=True
                )
                print(f"Auto-rotation restored to original setting: {self.original_orientation_lock}")
            else:
                # If we couldn't get the original setting, just set it to false
                subprocess.run(
                    ['gsettings', 'set', 'org.gnome.settings-daemon.peripherals.touchscreen', 'orientation-lock', 'false'],
                    check=True
                )
                print("Auto-rotation enabled (default)")
        except Exception as e:
            print(f"Failed to enable auto-rotation: {e}")
        
    def initialize_camera(self):
        if self.camera_manager.initialize():
            # Start continuous update loop after camera is initialized
            GLib.idle_add(self.update_frame)
            return False
        else:
            print("Camera initialization failed!")
            return False
        
    def update_frame(self):
        try:
            ret, frame, frame_raw, info = self.camera_manager.read_frame()
            if not ret:
                print("Failed to read frame in update_frame")
                return True  # Keep the loop running even if we fail
                
            # Process frame with current settings
            processed_frame = self.image_processor.process_frame(frame, info)
            
            # Write frame if recording
            self.recorder.write_frame(processed_frame)
            self.recorder.write_raw_frame(frame_raw)
            
            # Update display
            self.thermal_view.update_frame(processed_frame, frame_raw)
            return True
        except Exception as e:
            print(f"Error in update_frame: {e}")
            return True
            
    def save_screenshot(self):
        if self.thermal_view.current_frame is not None:
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.png'
            save_path = Path(get_pictures_dir()) / filename
            cv2.imwrite(str(save_path), self.thermal_view.current_frame)
            print(f"Screenshot saved as {save_path}")
            
    def on_window_close(self, window):
        # Clean up wake lock inhibitor
        self.disable_wake_lock()
        # Restore auto-rotation
        self.enable_auto_rotation()
        
        self.recorder.cleanup()
        self.camera_manager.release()
        self.get_application().quit()
        return True

    def on_drag_begin(self, gesture, start_x, start_y):
        # Start window dragging using the root surface
        surface = self.get_surface()
        if surface:
            device = gesture.get_device()
            surface.begin_move(
                device,
                gesture.get_current_button(),
                int(start_x),
                int(start_y),
                gesture.get_current_event_time()
            )
        
    def on_drag_update(self, gesture, offset_x, offset_y):
        # This is needed to handle the drag update event, but we don't need to do anything here
        pass 