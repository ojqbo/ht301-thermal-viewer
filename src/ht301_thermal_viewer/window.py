import gi
import cv2
import time
from gi.repository import Gtk, GLib, Adw, Gdk

from .thermal_view import ThermalView
from .camera_manager import CameraManager
from .image_processor import ImageProcessor
from .recorder import Recorder
from .controls_manager import ControlsManager
from .styles import apply_css

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
        apply_css()
        
        # Set window content
        self.set_content(self.main_box)
        
        # Connect window signals
        self.connect("close-request", self.on_window_close)
        self.connect("realize", self.on_window_realize)
        
        
    def on_window_realize(self, window):
        # Initialize camera after window is realized
        GLib.idle_add(self.initialize_camera)
        
    def initialize_camera(self):
        if self.camera_manager.initialize():
            # Start continuous update loop after camera is initialized
            GLib.idle_add(self.update_frame)
            return False
        else:
            print("Camera initialization failed!")
            # Try to show an error dialog to the user
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Camera Error",
                secondary_text="Failed to initialize the thermal camera. Please check the connection and try again."
            )
            dialog.connect("response", lambda dialog, response: dialog.destroy())
            dialog.show()
            return False
        
    def update_frame(self):
        try:
            ret, frame, info = self.camera_manager.read_frame()
            if not ret:
                print("Failed to read frame in update_frame")
                return True  # Keep the loop running even if we fail
                
            # Process frame with current settings
            processed_frame = self.image_processor.process_frame(frame, info)
            
            # Write frame if recording
            self.recorder.write_frame(processed_frame)
            
            # Update display
            self.thermal_view.update_frame(processed_frame)
            return True
        except Exception as e:
            print(f"Error in update_frame: {e}")
            return True
            
    def save_screenshot(self):
        if self.thermal_view.current_frame is not None:
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.png'
            cv2.imwrite(filename, self.thermal_view.current_frame)
            print(f"Screenshot saved as {filename}")
            
    def on_window_close(self, window):
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