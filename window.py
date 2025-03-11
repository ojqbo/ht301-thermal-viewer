import gi
import cv2
import time
import os
import numpy as np
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf, Adw

import ht301_hacklib
import utils
from thermal_view import ThermalView
from shutter_button import ShutterButton
from styles import apply_css

class ThermalCameraWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize camera
        self.cap = None
        self.draw_temp = True
        
        # Image transformation states
        self.flip_horizontal = False
        self.flip_vertical = False
        self.rotation = 0  # 0, 90, 180, 270 degrees
        
        # Recording state
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        
        # Initialize colormap settings
        self.colormaps = [
            ('NO_MAP', None),  # Add NO_MAP option with None as the colormap value
            ('JET', cv2.COLORMAP_JET),
            ('HOT', cv2.COLORMAP_HOT),
            ('INFERNO', cv2.COLORMAP_INFERNO),
            ('PLASMA', cv2.COLORMAP_PLASMA),
            ('VIRIDIS', cv2.COLORMAP_VIRIDIS),
            ('MAGMA', cv2.COLORMAP_MAGMA),
            ('RAINBOW', cv2.COLORMAP_RAINBOW),
            ('BONE', cv2.COLORMAP_BONE),
        ]
        self.current_colormap_idx = 0  # Start with NO_MAP
        
        # Set window properties
        self.set_default_size(800, 600)
        self.set_size_request(384, 288)  # Minimum size based on thermal camera resolution
        
        # Create main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("main-box")
        
        # Create thermal view
        self.thermal_view = ThermalView()
        self.main_box.append(self.thermal_view)
        
        self._setup_controls()
        
        # Apply CSS styles
        apply_css()
        
        # Set window content
        self.set_content(self.main_box)
        
        # Connect window close signal
        self.connect("close-request", self.on_window_close)
        
        # Connect to realize signal to ensure window is ready
        self.connect("realize", self.on_window_realize)
        
    def _setup_controls(self):
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
        temp_toggle_button.set_icon_name("zoom-fit-best-symbolic")
        temp_toggle_button.add_css_class("circular")
        temp_toggle_button.add_css_class("flat")
        temp_toggle_button.add_css_class("temp-toggle-button")
        temp_toggle_button.set_active(self.draw_temp)
        temp_toggle_button.connect("toggled", self.on_temp_toggle)
        temp_toggle_button.set_tooltip_text("Toggle Temperature Display")
        top_controls.append(temp_toggle_button)
        
        # Add colormap toggle button
        colormap_button = Gtk.MenuButton()
        colormap_button.set_icon_name("color-select-symbolic")
        colormap_button.add_css_class("circular")
        colormap_button.add_css_class("flat")
        colormap_button.add_css_class("colormap-button")
        
        # Create popover menu for colormaps
        popover = Gtk.Popover()
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.add_css_class("colormap-popover")
        
        # Create grid for colormap options
        colormap_grid = Gtk.Grid()
        colormap_grid.set_row_spacing(4)
        colormap_grid.set_column_spacing(4)
        colormap_grid.add_css_class("colormap-grid")
        
        # Add colormap options in a 3x3 grid
        for idx, (name, _) in enumerate(self.colormaps):
            # Create button with icon and label
            colormap_btn = Gtk.Button()
            colormap_btn.add_css_class("colormap-option")
            colormap_btn.add_css_class("flat")
            colormap_btn.set_hexpand(True)
            colormap_btn.set_vexpand(True)
            
            # Create overlay for the button content
            overlay = Gtk.Overlay()
            overlay.set_hexpand(True)
            overlay.set_vexpand(True)
            
            # Load and set icon
            icon_path = f"cmaps/{name}.png"
            if os.path.exists(icon_path):
                # Create a Picture widget instead of Image for better scaling
                picture = Gtk.Picture.new_for_filename(icon_path)
                picture.set_can_shrink(True)
                picture.set_keep_aspect_ratio(False)
                picture.set_hexpand(True)
                picture.set_vexpand(True)
                picture.add_css_class("colormap-preview")
                overlay.set_child(picture)
            
            # Add label
            label = Gtk.Label(label=name)
            label.set_halign(Gtk.Align.FILL)
            label.set_valign(Gtk.Align.END)
            label.set_hexpand(True)
            label.set_size_request(-1, 40)  # Set minimum height for the label
            label.add_css_class("colormap-label")
            overlay.add_overlay(label)
            
            colormap_btn.set_child(overlay)
            
            if idx == self.current_colormap_idx:
                colormap_btn.add_css_class("selected")
            
            colormap_btn.connect("clicked", self.on_colormap_selected, idx)
            
            # Add to grid
            row = idx // 3
            col = idx % 3
            colormap_grid.attach(colormap_btn, col, row, 1, 1)
        
        popover.set_child(colormap_grid)
        colormap_button.set_popover(popover)
        colormap_button.set_tooltip_text(f"Select Colormap (Current: {self.colormaps[self.current_colormap_idx][0]})")
        top_controls.append(colormap_button)
        
        # Add transform button
        transform_button = Gtk.MenuButton()
        transform_button.set_icon_name("object-flip-horizontal-symbolic")
        transform_button.add_css_class("circular")
        transform_button.add_css_class("flat")
        transform_button.add_css_class("transform-button")
        
        # Create popover for transform options
        transform_popover = Gtk.Popover()
        transform_popover.set_position(Gtk.PositionType.BOTTOM)
        transform_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        transform_box.set_margin_start(4)
        transform_box.set_margin_end(4)
        transform_box.set_margin_top(4)
        transform_box.set_margin_bottom(4)
        
        # Add transform buttons
        flip_h_btn = Gtk.Button(label="Flip Horizontally")
        flip_h_btn.add_css_class("flat")
        flip_h_btn.set_icon_name("object-flip-horizontal-symbolic")
        flip_h_btn.connect("clicked", self.on_flip_horizontal)
        transform_box.append(flip_h_btn)
        
        flip_v_btn = Gtk.Button(label="Flip Vertically")
        flip_v_btn.add_css_class("flat")
        flip_v_btn.set_icon_name("object-flip-vertical-symbolic")
        flip_v_btn.connect("clicked", self.on_flip_vertical)
        transform_box.append(flip_v_btn)
        
        rotate_cw_btn = Gtk.Button(label="Rotate Clockwise")
        rotate_cw_btn.add_css_class("flat")
        rotate_cw_btn.set_icon_name("object-rotate-right-symbolic")
        rotate_cw_btn.connect("clicked", self.on_rotate_clockwise)
        transform_box.append(rotate_cw_btn)
        
        rotate_ccw_btn = Gtk.Button(label="Rotate Counterclockwise")
        rotate_ccw_btn.add_css_class("flat")
        rotate_ccw_btn.set_icon_name("object-rotate-left-symbolic")
        rotate_ccw_btn.connect("clicked", self.on_rotate_counterclockwise)
        transform_box.append(rotate_ccw_btn)
        
        transform_popover.set_child(transform_box)
        transform_button.set_popover(transform_popover)
        transform_button.set_tooltip_text("Image Transformations")
        top_controls.append(transform_button)
        
        # Add shutter button
        self.shutter_button = ShutterButton()
        self.shutter_button.connect("clicked", self.on_screenshot_clicked)
        controls.append(self.shutter_button)
        
        # Add record button
        self.record_button = Gtk.ToggleButton()
        self.record_button.set_icon_name("media-record-symbolic")
        self.record_button.add_css_class("circular")
        self.record_button.add_css_class("flat")
        self.record_button.add_css_class("record-button")
        self.record_button.connect("toggled", self.on_record_toggled)
        self.record_button.set_tooltip_text("Start Recording")
        controls.append(self.record_button)
        
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
        
    def on_calibrate_clicked(self, button):
        if self.cap:
            self.cap.calibrate()
            
    def on_temp_toggle(self, button):
        self.draw_temp = button.get_active()
                
    def on_colormap_selected(self, button, idx):
        # Remove selected class from previous button
        grid = button.get_parent()  # Get the grid
        for child in grid:
            child.remove_css_class("selected")
        
        # Add selected class to clicked button
        button.add_css_class("selected")
        
        # Update colormap
        self.current_colormap_idx = idx
        
        # Update tooltip on main colormap button
        popover = button.get_ancestor(Gtk.Popover)
        menu_button = popover.get_parent()
        if menu_button:
            menu_button.set_tooltip_text(f"Select Colormap (Current: {self.colormaps[self.current_colormap_idx][0]})")
        
        # Close the popover
        if popover:
            popover.set_visible(False)
                
    def on_screenshot_clicked(self, button):
        if self.thermal_view.current_frame is not None:
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.png'
            cv2.imwrite(filename, self.thermal_view.current_frame)
            
    def on_window_close(self, window):
        if self.video_writer is not None:
            self.video_writer.release()
        if self.cap:
            self.cap.release()
        self.get_application().quit()
        return True
        
    def on_record_toggled(self, button):
        if button.get_active():
            # Get current frame to determine dimensions
            if self.thermal_view.current_frame is None:
                print("Error: No frame available to start recording")
                return
                
            # Get dimensions from current frame
            height, width = self.thermal_view.current_frame.shape[:2]
            
            # Start recording
            filename = time.strftime("%Y-%m-%d_%H:%M:%S") + '.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 25.0, (width, height))
            self.recording_start_time = time.time()
            self.is_recording = True
            button.set_icon_name("media-playback-stop-symbolic")
            button.set_tooltip_text("Stop Recording")
            button.add_css_class("recording")
        else:
            # Stop recording
            self.is_recording = False
            if self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None
            button.set_icon_name("media-record-symbolic")
            button.set_tooltip_text("Start Recording")
            button.remove_css_class("recording")
        
    def on_flip_horizontal(self, button):
        self.flip_horizontal = not self.flip_horizontal
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def on_flip_vertical(self, button):
        self.flip_vertical = not self.flip_vertical
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def on_rotate_clockwise(self, button):
        self.rotation = (self.rotation + 90) % 360
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def on_rotate_counterclockwise(self, button):
        self.rotation = (self.rotation - 90) % 360
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def apply_transformations(self, frame):
        # Apply flips
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)
        if self.flip_vertical:
            frame = cv2.flip(frame, 0)
            
        # Apply rotation
        if self.rotation != 0:
            if self.rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif self.rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame

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
            
            # Only apply colormap if not using NO_MAP
            if self.colormaps[self.current_colormap_idx][1] is not None:
                frame = cv2.applyColorMap(frame, self.colormaps[self.current_colormap_idx][1])
            else:
                # For NO_MAP, convert grayscale to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            # Apply transformations
            frame = self.apply_transformations(frame)
            
            if self.draw_temp:
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
            
            # Write frame if recording
            if self.is_recording and self.video_writer is not None:
                self.video_writer.write(frame)
                
            self.thermal_view.update_frame(frame)
            return True
        except Exception as e:
            print(f"Error updating frame: {e}")
            return True 