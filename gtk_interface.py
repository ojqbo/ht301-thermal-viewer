# This file has been refactored into separate modules:
# - main.py: Main entry point
# - app.py: Application class
# - window.py: Main window class
# - thermal_view.py: Thermal view widget
# - styles.py: CSS styles

from main import main

if __name__ == '__main__':
    exit_code = main() 