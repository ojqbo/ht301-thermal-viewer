import gi
import cairo
import cv2
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

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
        
    def update_frame(self, frame, frame_raw):
        self.current_frame = frame
        self.frame_raw = frame_raw
        self.frame_count += 1
        self.status_label.set_visible(False)
        self.drawing_area.queue_draw()
        
    def on_draw(self, drawing_area, cr, width, height):
        if self.current_frame is None:
            # Show error message with proper styling
            self.status_label.set_visible(True)
            self.status_label.set_text("Failed to initialize the thermal camera. Please check the connection and try again.")
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