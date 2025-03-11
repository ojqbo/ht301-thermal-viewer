import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw

from .window import ThermalCameraWindow

class ThermalCameraApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.thermalcam.app')
        self.window = None
        
    def do_activate(self):
        if not self.window:
            self.window = ThermalCameraWindow(application=self)
            self.window.present() 