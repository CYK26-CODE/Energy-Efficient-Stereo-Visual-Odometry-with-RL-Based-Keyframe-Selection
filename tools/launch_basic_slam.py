#!/usr/bin/env python3
"""
Basic SLAM with 2D Trajectory Overlay
Launches integrated_slam.py with dynamic IP configuration
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))
sys.path.insert(0, str(ROOT))

from dynamic_ip_config import DynamicIPConfig
import cv2
import numpy as np
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

from stereo_slam import StereoSLAMSystem


def main():
    print("="*70)
    print(" "*15 + "BASIC SLAM WITH 2D OVERLAY")
    print("="*70)
    
    # Get camera configuration
    config = DynamicIPConfig()
    if not config.show_config_dialog("Basic SLAM System"):
        print("\n❌ Cancelled by user")
        return
    
    # Setup cameras
    if config.use_synthetic:
        print("\n✓ Using Synthetic Cameras")
        from ultimate_slam_rl_gui import SyntheticStereoCameraManager
        camera_manager = SyntheticStereoCameraManager()
    else:
        print(f"\n✓ Using Real ESP32 Cameras")
        print(f"   Left:  {config.left_url}")
        print(f"   Right: {config.right_url}")
        
        from camera_stream_handler import StereoCameraManager
        camera_manager = StereoCameraManager(config.left_url, config.right_url)
    
    # Initialize SLAM
    slam_system = StereoSLAMSystem(max_keyframes=100, min_displacement=0.05)
    
    print("\n🚀 Starting Basic SLAM System...")
    print("   Controls: 'q' = quit, 's' = save map\n")
    
    # Start cameras
    if not camera_manager.start():
        print("❌ Could not start cameras")
        return
    
    # Main loop
    running = True
    frame_count = 0
    
    try:
        while running:
            stereo_pair = camera_manager.get_stereo_pair()
            if stereo_pair is None:
                time.sleep(0.01)
                continue
            
            left_frame, right_frame = stereo_pair
            frame_count += 1
            
            # Process SLAM
            is_keyframe = slam_system.process_stereo_pair(left_frame, right_frame, time.time())
            
            # Create display with 2D overlay
            display = create_display_with_overlay(left_frame, right_frame, slam_system, is_keyframe)
            
            cv2.imshow("Basic SLAM with 2D Overlay", display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                slam_system.save_map("basic_slam_map.json")
                print("✓ Map saved!")
    
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    finally:
        camera_manager.stop()
        cv2.destroyAllWindows()
        print("\n✓ System shutdown complete")


def create_display_with_overlay(left, right, slam_system, is_keyframe):
    """Create display with 2D trajectory overlay"""
    h, w = left.shape[:2]
    target_h = 600
    target_w = int(target_h * w / h)
    
    left_resized = cv2.resize(left.copy(), (target_w, target_h))
    right_resized = cv2.resize(right, (target_w, target_h))
    
    # Add 2D overlay
    trajectory = slam_system.get_trajectory()
    if len(trajectory) > 1:
        traj_2d = trajectory[:, :2]
        min_x, min_y = traj_2d.min(axis=0)
        max_x, max_y = traj_2d.max(axis=0)
        
        overlay_size = 150
        margin = 10
        
        if (max_x - min_x) > 1e-6 and (max_y - min_y) > 1e-6:
            scale = (overlay_size - 2*margin) / max(max_x - min_x, max_y - min_y)
            traj_scaled = (traj_2d - [min_x, min_y]) * scale + margin
            
            overlay = np.zeros((overlay_size + 2*margin, overlay_size + 2*margin, 3), dtype=np.uint8)
            overlay[:] = [30, 30, 30]
            
            # Grid
            for i in range(0, overlay_size + 2*margin, 30):
                cv2.line(overlay, (i, 0), (i, overlay_size + 2*margin), (60, 60, 60), 1)
                cv2.line(overlay, (0, i), (overlay_size + 2*margin, i), (60, 60, 60), 1)
            
            # Path
            for i in range(len(traj_scaled) - 1):
                pt1 = tuple(traj_scaled[i].astype(int))
                pt2 = tuple(traj_scaled[i + 1].astype(int))
                color = (int(255 * (i / len(traj_scaled))), 100, int(100 + 155 * (i / len(traj_scaled))))
                cv2.line(overlay, pt1, pt2, color, 2)
            
            cv2.circle(overlay, tuple(traj_scaled[0].astype(int)), 5, (0, 255, 0), -1)
            cv2.circle(overlay, tuple(traj_scaled[-1].astype(int)), 5, (0, 0, 255), -1)
            cv2.rectangle(overlay, (0, 0), (overlay_size + 2*margin - 1, overlay_size + 2*margin - 1), (100, 150, 255), 2)
            
            left_resized[0:overlay.shape[0], 0:overlay.shape[1]] = \
                cv2.addWeighted(left_resized[0:overlay.shape[0], 0:overlay.shape[1]], 0.6, overlay, 0.4, 0)
    
    # Combine
    separator = np.ones((target_h, 40, 3), dtype=np.uint8) * 50
    cv2.line(separator, (20, 0), (20, target_h), (100, 100, 255), 2)
    composite = np.hstack([left_resized, separator, right_resized])
    
    # Info bar
    info_bar = np.ones((100, composite.shape[1], 3), dtype=np.uint8) * 20
    composite = np.vstack([info_bar, composite])
    
    # Stats
    kf_info = slam_system.get_keyframes_info()
    cv2.putText(composite, "BASIC SLAM WITH 2D OVERLAY", (20, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 150), 2)
    cv2.putText(composite, f"Frames: {kf_info['frames_processed']} | Keyframes: {kf_info['total_keyframes']} | Points: {kf_info['total_points']}",
               (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
    
    status = "🔑 KEYFRAME" if is_keyframe else "→ TRACKING"
    color = (0, 255, 0) if is_keyframe else (100, 150, 255)
    cv2.putText(composite, status, (composite.shape[1] - 300, 65),
               cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    return composite


if __name__ == "__main__":
    main()
