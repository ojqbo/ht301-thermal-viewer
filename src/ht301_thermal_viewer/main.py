#!/usr/bin/python3
from .app import ThermalCameraApp

def main():
    try:
        app = ThermalCameraApp()
        return app.run(None)
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main() 