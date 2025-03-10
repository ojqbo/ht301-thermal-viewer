import gi
import math
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Gdk

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
