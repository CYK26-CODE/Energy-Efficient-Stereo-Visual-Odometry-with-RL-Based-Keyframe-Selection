#!/usr/bin/env python3
"""
Complete SLAM + RL System with Dynamic IP Configuration
Launches the full integrated system with GUI controls
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))
sys.path.insert(0, str(ROOT))

from dynamic_ip_config import DynamicIPConfig


def main():
    print("="*70)
    print(" "*15 + "COMPLETE SLAM + RL SYSTEM")
    print("="*70)
    
    # Get camera configuration
    config = DynamicIPConfig()
    
    # Build URLs immediately if not using synthetic
    if not config.use_synthetic and config.left_ip and config.right_ip:
        config.left_url = f"http://{config.left_ip}/stream"
        config.right_url = f"http://{config.right_ip}/stream"
    
    # Show dialog
    if not config.show_config_dialog("Complete SLAM + RL System"):
        print("\n❌ Cancelled by user")
        return
    
    # Import system
    from ultimate_slam_rl_gui import UltimateSLAMRLSystem
    
    if config.use_synthetic:
        print("\n✓ Using Synthetic Cameras")
        system = UltimateSLAMRLSystem(use_synthetic=True)
    else:
        print(f"\n✓ Using Real ESP32 Cameras")
        print(f"   Left:  {config.left_url}")
        print(f"   Right: {config.right_url}")
        
        from camera_stream_handler import StereoCameraManager
        system = UltimateSLAMRLSystem(use_synthetic=False)
        system.camera_manager = StereoCameraManager(config.left_url, config.right_url)
    
    print("\n🚀 Starting Complete SLAM + RL System...\n")
    system.start()


if __name__ == "__main__":
    main()
