#!/usr/bin/env python3
"""
Backend SLAM Runner - Uses synthetic stereo data
"""

import sys
from pathlib import Path

# Setup paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app' / 'backend'))
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))

# Import and run
from integrated_slam import IntegratedStereoSLAMSystem
from app.runtime.synthetic_stereo import MockCameraStream

def run_backend_with_synthetic():
    """Run backend SLAM with synthetic stereo data"""
    print("\n" + "="*80)
    print("🔴 BACKEND SLAM SYSTEM - SYNTHETIC DATA MODE")
    print("="*80)
    print("\n📊 System Configuration:")
    print("   • Camera Source: SYNTHETIC STEREO")
    print("   • Processing Mode: Full SLAM with loop closure")
    print("   • Battery Management: Enabled")
    print("   • Visualization: Real-time 3D")
    print("\n" + "="*80 + "\n")
    
    # Create SLAM system
    system = IntegratedStereoSLAMSystem(
        left_camera_url='synthetic://left',
        right_camera_url='synthetic://right'
    )
    
    # Replace camera manager with mock
    mock_camera = MockCameraStream()
    system.camera_manager = type('CameraManager', (), {
        'start': lambda: mock_camera.start(),
        'get_stereo_pair': lambda: mock_camera.get_stereo_pair(),
        'is_ready': lambda: mock_camera.is_connected(),
        'stop': lambda: mock_camera.stop()
    })()
    
    # Run SLAM
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_backend_with_synthetic()
