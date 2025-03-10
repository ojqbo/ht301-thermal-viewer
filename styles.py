from gi.repository import Gtk, Gdk

def apply_css():
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
        .colormap-popover {
            background-color: rgba(40, 40, 40, 0.98);
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        .colormap-grid {
            margin: 4px;
            padding: 4px;
        }
        .colormap-option {
            padding: 0;
            margin: 4px;
            border-radius: 12px;
            transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
            min-width: 160px;
            min-height: 90px;
            background: none;
            border: 2px solid transparent;
            overflow: hidden;
            position: relative;
        }
        .colormap-preview {
            min-width: 160px;
            min-height: 90px;
            border-radius: 12px;
        }
        .colormap-option:hover {
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }
        .colormap-option.selected {
            border-color: rgba(255, 255, 255, 0.6);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        .colormap-label {
            color: rgba(255, 255, 255, 0.9);
            font-size: 13px;
            font-weight: 500;
            position: absolute;
            bottom: 8px;
            left: 0;
            right: 0;
            text-align: center;
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
            background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
            padding: 16px 8px 8px 8px;
            border-radius: 0 0 12px 12px;
        }
        .status-label {
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            padding: 8px;
            border-radius: 4px;
            margin: 8px;
        }
    """)
    
    # Get the default display
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        ) 