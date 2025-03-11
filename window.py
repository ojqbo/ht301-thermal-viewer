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
            
            # Only apply colormap if not using NO_MAP
            if self.colormaps[self.current_colormap_idx][1] is not None:
                frame = cv2.applyColorMap(frame, self.colormaps[self.current_colormap_idx][1])
            else:
                # For NO_MAP, convert to BGR format (grayscale to BGR)
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
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
        if self.cap:
            self.cap.release()
        self.get_application().quit()
        return True 