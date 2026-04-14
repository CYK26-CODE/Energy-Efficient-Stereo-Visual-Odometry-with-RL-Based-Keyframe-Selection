"""
Adaptive Camera Manager - tries real cameras, falls back to synthetic data
"""

import sys
from pathlib import Path
import time
import threading
from typing import Tuple, Optional
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / 'runtime'))

from camera_stream_handler import StereoCameraManager
from synthetic_stereo import MockCameraStream, SyntheticStereoGenerator


class AdaptiveCameraManager:
    """
    Intelligently manages camera sources:
    1. Try to connect to real ESP32 cameras
    2. If fails, automatically switch to synthetic data
    3. Provide seamless interface to SLAM
    """
    
    def __init__(self, left_url: str, right_url: str):
        """
        Initialize adaptive camera manager
        
        Args:
            left_url: Left camera URL (e.g., http://192.168.1.100/stream)
            right_url: Right camera URL (e.g., http://192.168.1.101/stream)
        """
        self.left_url = left_url
        self.right_url = right_url
        self.camera_manager = None
        self.mock_camera = None
        self.using_synthetic = False
        self.is_running = False
    
    def start(self) -> bool:
        """
        Start camera - try real first, then fallback to synthetic
        
        Returns:
            True if successful (real or synthetic)
        """
        print(f"\n🔌 Attempting to connect to real cameras...")
        print(f"   Left:  {self.left_url}")
        print(f"   Right: {self.right_url}")
        
        # Try real cameras first
        try:
            self.camera_manager = StereoCameraManager(self.left_url, self.right_url)
            self.camera_manager.left_camera.timeout = 3  # Reduce timeout
            self.camera_manager.right_camera.timeout = 3
            
            # Start and wait
            self.camera_manager.left_camera.start()
            self.camera_manager.right_camera.start()
            
            # Wait for connection
            start_time = time.time()
            timeout = 5
            while time.time() - start_time < timeout:
                if (self.camera_manager.left_camera.is_connected() and 
                    self.camera_manager.right_camera.is_connected()):
                    print("✅ REAL cameras connected successfully!\n")
                    self.is_running = True
                    return True
                time.sleep(0.5)
            
            # Real cameras failed
            print("❌ Could not connect to real cameras (timeout)")
            self.camera_manager.stop()
            self.camera_manager = None
        
        except Exception as e:
            print(f"❌ Real camera connection failed: {e}")
            self.camera_manager = None
        
        # Fallback to synthetic
        print("\n🎮 Switching to SYNTHETIC STEREO DATA...")
        print("   Running SLAM in simulation mode")
        print("   (Connect real ESP32 cameras to switch to live mode)\n")
        
        self.mock_camera = MockCameraStream()
        self.mock_camera.start()
        self.using_synthetic = True
        self.is_running = True
        return True
    
    def get_stereo_pair(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get next stereo frame pair"""
        if not self.is_running:
            return None
        
        if self.camera_manager:
            return self.camera_manager.get_stereo_pair()
        elif self.mock_camera:
            return self.mock_camera.get_stereo_pair()
        
        return None
    
    def is_ready(self) -> bool:
        """Check if camera source is ready"""
        if self.camera_manager:
            return self.camera_manager.is_ready()
        elif self.mock_camera:
            return self.mock_camera.is_connected()
        return False
    
    def stop(self):
        """Stop camera stream"""
        self.is_running = False
        if self.camera_manager:
            self.camera_manager.stop()
        if self.mock_camera:
            self.mock_camera.stop()
    
    def get_mode(self) -> str:
        """Get current mode (real or synthetic)"""
        return "SYNTHETIC" if self.using_synthetic else "REAL"
