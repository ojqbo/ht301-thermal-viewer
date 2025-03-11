# HT301 Thermal Camera Viewer

A modern GTK4 application for viewing and capturing thermal images from the HT301 thermal camera. Built with Python and GTK4 for a native GNOME experience.

![Demo on PC](screenshots/demo_PC_colormap_applied.png)

## Features

- 🎨 Multiple colormaps for thermal visualization
- 🔄 Image transformations (flip/rotate) for any camera orientation
- 🌡️ Temperature measurement points (min/max/center)
- 📸 Screenshot capture
- 🎥 Video recording
- 🖱️ Draggable window interface
- 💻 Cross-platform support (Linux, including mobile Linux distributions)

### Colormap Selection
Choose from various colormaps to enhance thermal visualization:

<details>
<summary>See colormap picker</summary>

![Colormap Picker](screenshots/demo_PC_colormap_picker.png)
</details>

### Image Transformations
Easily adjust camera orientation with transform tools. This is particularly useful when:
- Using the camera in selfie mode on mobile devices
- Using the camera with USB extension cables on PC
- Mounting the camera in different orientations

![Image Transforms](screenshots/demo_PC_image_transforms_cropped.png)

### Mobile Support
Works great on mobile Linux distributions like Mobian:

<details>
<summary>See mobile screenshot</summary>

![Demo on Mobian](screenshots/demo_Mobian.png)
</details>

## Installation

### System Dependencies

First, install the required system packages:
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-opencv python3-numpy
```

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/ojqbo/ht301-thermal-viewer.git
cd ht301-thermal-viewer
```

2. Run the installer script:
```bash
./install.sh
```

This will:
- Check for required system dependencies
- Install the application to your home directory (`~/.local`)
- Create a desktop entry for easy launching

After installation, you can run the application in two ways:
1. From your applications menu (search for "HT301 Thermal Viewer")
2. From the terminal:
```bash
ht301-thermal-viewer
```

Note: You may need to log out and back in for the application to appear in your applications menu.

### Uninstallation

To remove the application, run:
```bash
./uninstall.sh
```

This will remove all application files and desktop entries. Note that system dependencies (python3-gi, python3-opencv, etc.) are not removed by default as they might be needed by other applications.

### Running Without Installation

If you want to run the application directly from the source without installation, you can use:
```bash
PYTHONPATH=src python3 -c "from ht301_thermal_viewer.main import main; main()"
```

Note: This method requires you to be in the project root directory. The application uses relative imports for better package management, which is why we need to set PYTHONPATH to include the `src` directory.

## About

This application was developed as an experiment in programming with Agentic AI using [Cursor](https://www.cursor.com).

It has been tested with:

Operating Systems:
- Ubuntu 24.04
- Mobian (weekly image)

Cameras:
- HT301 thermal camera

## Credits

This application is based on:
- [ht301_hacklib](https://github.com/stawel/ht301_hacklib/) (GPL-3.0)
- [GNOME Snapshot](https://gitlab.gnome.org/GNOME/snapshot/) (GPL-3.0)

The app is released under the GPL-3.0 license.

## Contributing

Feel free to report issues or suggest improvements through GitHub issues. While I appreciate contributions, I may not be able to actively maintain pull requests due to time constraints.
