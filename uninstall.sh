#!/bin/bash

# Exit on error
set -e

echo "Uninstalling HT301 Thermal Camera Viewer..."

# Remove application files
echo "Removing application files..."
rm -rf ~/.local/lib/ht301-thermal-viewer

# Remove launcher script
echo "Removing launcher script..."
rm -f ~/.local/bin/ht301-thermal-viewer

# Remove desktop entry
echo "Removing desktop entry..."
rm -f ~/.local/share/applications/com.github.ojqbo.ht301-thermal-viewer.desktop

# Update desktop database
echo "Updating desktop database..."
update-desktop-database ~/.local/share/applications

echo "Uninstallation complete!"
echo "Note: System dependencies (python3-gi, python3-opencv, etc.) were not removed."
echo "If you want to remove them, run:"
echo "sudo apt-get remove python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-opencv python3-numpy" 