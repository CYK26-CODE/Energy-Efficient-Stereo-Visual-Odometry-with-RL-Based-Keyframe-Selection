"""
Camera Stream Handler Module
Handles fetching and decoding MJPEG streams from multiple camera sources
"""

import cv2
import numpy as np
import threading
import time
import requests
from collections import deque
from typing import Optional, Tuple

class CameraStreamHandler:
    """
    Manages streaming from multiple IP cameras with frame buffering
    """
    
    def __init__(self, camera_url: str, buffer_size: int = 2, timeout: int = 5):
        """
        Initialize camera stream handler
        
        Args:
            camera_url: URL to the camera stream (e.g., 'http://192.168.1.37/stream')
            buffer_size: Size of frame buffer
            timeout: Connection timeout in seconds
        """
        self.camera_url = camera_url
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.frame_buffer = deque(maxlen=buffer_size)
        self.latest_frame = None
        self.is_running = False
        self.thread = None
        self.error_count = 0
        self.max_errors = 5
        
    def start(self):
        """Start streaming thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._stream_worker, daemon=True)
            self.thread.start()
            print(f"Camera stream started: {self.camera_url}")
    
    def stop(self):
        """Stop streaming thread"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        print(f"Camera stream stopped: {self.camera_url}")
    
    def _stream_worker(self):
        """Worker thread for streaming"""
        try:
            response = requests.get(self.camera_url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            bytes_data = b''
            for chunk in response.iter_content(chunk_size=8192):
                if not self.is_running:
                    break
                    
                bytes_data += chunk
                
                # Find JPEG frame boundaries
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg_data = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    # Decode frame
                    frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        self.latest_frame = frame
                        self.frame_buffer.append(frame.copy())
                        self.error_count = 0
                    
        except Exception as e:
            self.error_count += 1
            print(f"Stream error ({self.camera_url}): {str(e)}")
            if self.error_count < self.max_errors:
                time.sleep(2)
                if self.is_running:
                    self._stream_worker()
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame from buffer"""
        return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def get_all_frames(self) -> list:
        """Get all frames in buffer"""
        return list(self.frame_buffer)
    
    def is_connected(self) -> bool:
        """Check if stream is active and receiving frames"""
        return self.is_running and self.latest_frame is not None


class StereoCameraManager:
    """
    Manages dual camera streams for stereo vision
    """
    
    def __init__(self, left_camera_url: str, right_camera_url: str):
        """
        Initialize stereo camera manager
        
        Args:
            left_camera_url: URL for left camera stream
            right_camera_url: URL for right camera stream
        """
        self.left_camera = CameraStreamHandler(left_camera_url)
        self.right_camera = CameraStreamHandler(right_camera_url)
    
    def start(self):
        """Start both camera streams"""
        self.left_camera.start()
        self.right_camera.start()
        
        # Wait for streams to initialize
        timeout = 10
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.left_camera.is_connected() and self.right_camera.is_connected():
                print("Both cameras connected successfully")
                return True
            time.sleep(0.5)
        
        print("Warning: Could not connect to both cameras within timeout")
        return False
    
    def stop(self):
        """Stop both camera streams"""
        self.left_camera.stop()
        self.right_camera.stop()
    
    def get_stereo_pair(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get synchronized stereo frame pair
        
        Returns:
            Tuple of (left_frame, right_frame) or None if not available
        """
        left_frame = self.left_camera.get_frame()
        right_frame = self.right_camera.get_frame()
        
        if left_frame is not None and right_frame is not None:
            return (left_frame, right_frame)
        return None
    
    def is_ready(self) -> bool:
        """Check if both cameras are ready"""
        return self.left_camera.is_connected() and self.right_camera.is_connected()
