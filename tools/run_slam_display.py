#!/usr/bin/env python3
"""
Run integrated_slam.py with synthetic stereo data
"""

import sys
from pathlib import Path

# Add paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))
sys.path.insert(0, str(ROOT / 'app' / 'frontend'))

# Patch camera_stream_handler to use synthetic data
from app.runtime.synthetic_stereo import SyntheticStereoGenerator

class SyntheticCameraStreamHandler:
    """Drop-in replacement for CameraStreamHandler using synthetic data"""
    
    def __init__(self, camera_url: str = "synthetic", buffer_size: int = 2, timeout: int = 5):
        self.camera_url = camera_url
        self.is_running = False
        self.latest_frame = None
        self.generator = None
    
    def start(self):
        self.is_running = True
        self.generator = SyntheticStereoGenerator()
        print(f"✅ Synthetic camera stream started (not using URL)")
        return True
    
    def stop(self):
        self.is_running = False
    
    def get_frame(self):
        if not self.is_running or not self.generator:
            return None
        # Generate next frame
        left, right = self.generator.generate_pair()
        self.latest_frame = left
        return left
    
    def is_connected(self):
        return self.is_running and self.generator is not None


class SyntheticStereoCameraManager:
    """Drop-in replacement for StereoCameraManager using synthetic data"""
    
    def __init__(self, left_camera_url: str = "synthetic_left", right_camera_url: str = "synthetic_right"):
        self.left_camera = SyntheticCameraStreamHandler(left_camera_url)
        self.right_camera = SyntheticCameraStreamHandler(right_camera_url)
        self.current_left = None
        self.current_right = None
    
    def start(self):
        self.left_camera.start()
        self.right_camera.start()
        print("✅ Synthetic stereo camera manager started")
        return True
    
    def stop(self):
        self.left_camera.stop()
        self.right_camera.stop()
    
    def get_stereo_pair(self):
        # Generate one pair (both from same generator for consistency)
        if not self.left_camera.is_connected():
            return None
        
        left = self.left_camera.get_frame()
        right = self.right_camera.get_frame()
        
        if left is not None and right is not None:
            return (left, right)
        return None
    
    def is_ready(self):
        return self.left_camera.is_connected() and self.right_camera.is_connected()


# Monkey-patch the camera_stream_handler module
from app.runtime import camera_stream_handler
camera_stream_handler.StereoCameraManager = SyntheticStereoCameraManager

# Now import and run integrated_slam
from app.runtime.integrated_slam import IntegratedStereoSLAMSystem

if __name__ == "__main__":
    print("\n" + "="*70)
    print("INTEGRATED STEREO SLAM - SYNTHETIC DATA MODE")
    print("="*70)
    print("\nGenerating synthetic stereo camera feeds...")
    
    # Create system with dummy URLs (will use synthetic)
    system = IntegratedStereoSLAMSystem(
        left_camera_url="synthetic_left",
        right_camera_url="synthetic_right"
    )
    
    # Run the system
    system.run()
