import os
from gi.repository import Gtk, GdkPixbuf
from shutter_button import ShutterButton

class ControlsManager:
    def __init__(self, window, image_processor, camera_manager, recorder):
        self.window = window
        self.image_processor = image_processor
        self.camera_manager = camera_manager
        self.recorder = recorder
        
        # Create controls containers
        self.controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.controls.set_halign(Gtk.Align.CENTER)
        self.controls.set_valign(Gtk.Align.END)
        self.controls.set_margin_bottom(16)
        self.controls.add_css_class("controls")
        self.controls.add_css_class("controls-container")
        
        self.top_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.top_controls.set_halign(Gtk.Align.END)
        self.top_controls.set_valign(Gtk.Align.START)
        self.top_controls.set_margin_top(16)
        self.top_controls.set_margin_end(16)
        self.top_controls.add_css_class("controls")
        self.top_controls.add_css_class("controls-container")
        
        self._setup_top_controls()
        self._setup_bottom_controls()
        
    def _setup_top_controls(self):
        # Temperature toggle button
        temp_toggle = Gtk.ToggleButton()
        temp_toggle.set_icon_name("zoom-fit-best-symbolic")
        temp_toggle.add_css_class("circular")
        temp_toggle.add_css_class("flat")
        temp_toggle.add_css_class("temp-toggle-button")
        temp_toggle.set_active(self.image_processor.draw_temp)
        temp_toggle.connect("toggled", self._on_temp_toggle)
        temp_toggle.set_tooltip_text("Toggle Temperature Display")
        self.top_controls.append(temp_toggle)
        
        # Colormap button
        colormap_button = self._create_colormap_button()
        self.top_controls.append(colormap_button)
        
        # Transform button
        transform_button = self._create_transform_button()
        self.top_controls.append(transform_button)
        
    def _setup_bottom_controls(self):
        # Shutter button
        self.shutter_button = ShutterButton()
        self.shutter_button.connect("clicked", self._on_screenshot_clicked)
        self.controls.append(self.shutter_button)
        
        # Record button
        self.record_button = Gtk.ToggleButton()
        self.record_button.set_icon_name("media-record-symbolic")
        self.record_button.add_css_class("circular")
        self.record_button.add_css_class("flat")
        self.record_button.add_css_class("record-button")
        self.record_button.connect("toggled", self._on_record_toggled)
        self.record_button.set_tooltip_text("Start Recording")
        self.controls.append(self.record_button)
        
        # Calibrate button
        calibrate_button = Gtk.Button()
        calibrate_button.set_icon_name("view-refresh-symbolic")
        calibrate_button.add_css_class("circular")
        calibrate_button.add_css_class("flat")
        calibrate_button.add_css_class("calibrate-button")
        calibrate_button.connect("clicked", self._on_calibrate_clicked)
        calibrate_button.set_tooltip_text("Calibrate")
        self.controls.append(calibrate_button)
        
    def _create_colormap_button(self):
        button = Gtk.MenuButton()
        button.set_icon_name("color-select-symbolic")
        button.add_css_class("circular")
        button.add_css_class("flat")
        button.add_css_class("colormap-button")
        
        popover = Gtk.Popover()
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.add_css_class("colormap-popover")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(4)
        grid.add_css_class("colormap-grid")
        
        for idx, (name, _) in enumerate(self.image_processor.colormaps):
            colormap_btn = self._create_colormap_grid_button(name, idx)
            row = idx // 3
            col = idx % 3
            grid.attach(colormap_btn, col, row, 1, 1)
            
        popover.set_child(grid)
        button.set_popover(popover)
        button.set_tooltip_text(f"Select Colormap (Current: {self.image_processor.get_current_colormap_name()})")
        return button
        
    def _create_colormap_grid_button(self, name, idx):
        btn = Gtk.Button()
        btn.add_css_class("colormap-option")
        btn.add_css_class("flat")
        btn.set_hexpand(True)
        btn.set_vexpand(True)
        
        overlay = Gtk.Overlay()
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)
        
        icon_path = f"cmaps/{name}.png"
        if os.path.exists(icon_path):
            picture = Gtk.Picture.new_for_filename(icon_path)
            picture.set_can_shrink(True)
            picture.set_keep_aspect_ratio(False)
            picture.set_hexpand(True)
            picture.set_vexpand(True)
            picture.add_css_class("colormap-preview")
            overlay.set_child(picture)
            
        label = Gtk.Label(label=name)
        label.set_halign(Gtk.Align.FILL)
        label.set_valign(Gtk.Align.END)
        label.set_hexpand(True)
        label.set_size_request(-1, 40)
        label.add_css_class("colormap-label")
        overlay.add_overlay(label)
        
        btn.set_child(overlay)
        
        if idx == self.image_processor.current_colormap_idx:
            btn.add_css_class("selected")
            
        btn.connect("clicked", self._on_colormap_selected, idx)
        return btn
        
    def _create_transform_button(self):
        button = Gtk.MenuButton()
        button.set_icon_name("view-more-symbolic")
        button.add_css_class("circular")
        button.add_css_class("flat")
        button.add_css_class("transform-button")
        
        popover = Gtk.Popover()
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.add_css_class("transform-popover")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_start(4)
        box.set_margin_end(4)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        
        flip_h_btn = Gtk.Button(label="Flip Horizontally")
        flip_h_btn.add_css_class("flat")
        flip_h_btn.set_icon_name("object-flip-horizontal-symbolic")
        flip_h_btn.connect("clicked", self._on_flip_horizontal)
        box.append(flip_h_btn)
        
        flip_v_btn = Gtk.Button(label="Flip Vertically")
        flip_v_btn.add_css_class("flat")
        flip_v_btn.set_icon_name("object-flip-vertical-symbolic")
        flip_v_btn.connect("clicked", self._on_flip_vertical)
        box.append(flip_v_btn)
        
        rotate_cw_btn = Gtk.Button(label="Rotate Clockwise")
        rotate_cw_btn.add_css_class("flat")
        rotate_cw_btn.set_icon_name("object-rotate-right-symbolic")
        rotate_cw_btn.connect("clicked", self._on_rotate_clockwise)
        box.append(rotate_cw_btn)
        
        rotate_ccw_btn = Gtk.Button(label="Rotate Counterclockwise")
        rotate_ccw_btn.add_css_class("flat")
        rotate_ccw_btn.set_icon_name("object-rotate-left-symbolic")
        rotate_ccw_btn.connect("clicked", self._on_rotate_counterclockwise)
        box.append(rotate_ccw_btn)
        
        popover.set_child(box)
        button.set_popover(popover)
        button.set_tooltip_text("Image Transformations")
        return button
        
    # Event handlers
    def _on_temp_toggle(self, button):
        self.image_processor.draw_temp = button.get_active()
        
    def _on_colormap_selected(self, button, idx):
        grid = button.get_parent()
        for child in grid:
            child.remove_css_class("selected")
        button.add_css_class("selected")
        
        self.image_processor.current_colormap_idx = idx
        
        popover = button.get_ancestor(Gtk.Popover)
        menu_button = popover.get_parent()
        if menu_button:
            menu_button.set_tooltip_text(f"Select Colormap (Current: {self.image_processor.get_current_colormap_name()})")
            
        if popover:
            popover.set_visible(False)
            
    def _on_screenshot_clicked(self, button):
        self.window.save_screenshot()
        
    def _on_record_toggled(self, button):
        if button.get_active():
            if self.recorder.start_recording(self.window.thermal_view.current_frame):
                button.set_icon_name("media-playback-stop-symbolic")
                button.set_tooltip_text("Stop Recording")
                button.add_css_class("recording")
        else:
            self.recorder.stop_recording()
            button.set_icon_name("media-record-symbolic")
            button.set_tooltip_text("Start Recording")
            button.remove_css_class("recording")
            
    def _on_calibrate_clicked(self, button):
        self.camera_manager.calibrate()
        
    def _on_flip_horizontal(self, button):
        self.image_processor.flip_horizontal = not self.image_processor.flip_horizontal
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def _on_flip_vertical(self, button):
        self.image_processor.flip_vertical = not self.image_processor.flip_vertical
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def _on_rotate_clockwise(self, button):
        self.image_processor.rotation = (self.image_processor.rotation + 90) % 360
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False)
            
    def _on_rotate_counterclockwise(self, button):
        self.image_processor.rotation = (self.image_processor.rotation - 90) % 360
        if button.get_ancestor(Gtk.Popover):
            button.get_ancestor(Gtk.Popover).set_visible(False) 