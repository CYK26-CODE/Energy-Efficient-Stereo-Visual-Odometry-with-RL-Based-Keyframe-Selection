"""
Launcher for Stereo SLAM
Core stereo SLAM implementation
"""

import sys
import os

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

runtime_path = os.path.join(application_path, 'app', 'runtime')
if os.path.exists(runtime_path):
    sys.path.insert(0, runtime_path)

def main():
    try:
        from stereo_slam import main as slam_main
        slam_main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
