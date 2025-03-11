#!/bin/bash

# Exit on error
set -e

echo "Installing HT301 Thermal Camera Viewer..."

# Check for required system packages
REQUIRED_PACKAGES="python3-gi python3-gi-cairo gir1.2-gtk-4.0 python3-opencv python3-numpy"

echo "Checking system dependencies..."
missing_packages=()
for pkg in $REQUIRED_PACKAGES; do
    if ! apt-cache policy "$pkg" 2>/dev/null | grep -q "Installed:.*[0-9]"; then
        missing_packages+=("$pkg")
    fi
done

if [ ${#missing_packages[@]} -ne 0 ]; then
    echo "Missing required packages: ${missing_packages[*]}"
    echo "Please install required packages first:"
    echo "sudo apt-get install $REQUIRED_PACKAGES"
    exit 1
fi

# Create installation directories
mkdir -p ~/.local/lib/ht301-thermal-viewer
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications

# Check if .local/bin is in PATH
if ! echo "$PATH" | tr ':' '\n' | grep -q "^$HOME/.local/bin$"; then
    echo "Warning: ~/.local/bin is not in your PATH"
    if [ ! -f "$HOME/.profile" ]; then
        echo "Recommendation: Copy the default .profile to your home directory to automatically add ~/.local/bin to your PATH"
        echo "Run the following command:"
        echo "cp /etc/skel/.profile ~/"
        echo "Then log out and log back in for the changes to take effect."
    fi
    echo "Note: You may need to add ~/.local/bin to your PATH manually or restart your session."
fi

# Copy the application files
cp -r src/ht301_thermal_viewer ~/.local/lib/ht301-thermal-viewer/
cp -r screenshots ~/.local/lib/ht301-thermal-viewer/

# Ensure colormap images are in the right place and have correct permissions
chmod -R +r ~/.local/lib/ht301-thermal-viewer/ht301_thermal_viewer/cmaps/*.png

# Create the launcher script
cat > ~/.local/bin/ht301-thermal-viewer << 'EOF'
#!/bin/bash
export PYTHONPATH="$HOME/.local/lib/ht301-thermal-viewer${PYTHONPATH:+:$PYTHONPATH}"
if [ -f "$HOME/.local/lib/ht301-thermal-viewer/ht301_thermal_viewer/main.py" ]; then
    cd "$HOME/.local/lib/ht301-thermal-viewer"
    exec python3 -c "from ht301_thermal_viewer.main import main; main()"
else
    echo "Error: Application files not found. Please reinstall the application."
    exit 1
fi
EOF

# Make the launcher executable
chmod +x ~/.local/bin/ht301-thermal-viewer

# Copy and update the desktop entry
cp thermalcamera.desktop ~/.local/share/applications/com.github.ojqbo.ht301-thermal-viewer.desktop
sed -i "s|Icon=screenshots/|Icon=$HOME/.local/lib/ht301-thermal-viewer/screenshots/|" ~/.local/share/applications/com.github.ojqbo.ht301-thermal-viewer.desktop

echo "Installation complete!"
echo "You can now run the application from your applications menu or by typing 'ht301-thermal-viewer' in the terminal."
echo "Note: You may need to log out and back in for the application to appear in your menu." 