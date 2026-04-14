#!/usr/bin/env python3
"""
Test script to verify integrated SLAM system is ready
"""

import sys
from pathlib import Path

# Add paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app' / 'frontend'))
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))
sys.path.insert(0, str(ROOT))

def test_imports():
    """Test all required imports"""
    print("\n" + "="*60)
    print("TESTING INTEGRATED SLAM SYSTEM")
    print("="*60 + "\n")
    
    tests = []
    
    # Test 1: Dashboard
    try:
        from main_dashboard import AdvancedDQNTrainingDashboard
        print("✅ Dashboard: AdvancedDQNTrainingDashboard")
        tests.append(("Dashboard", True))
    except Exception as e:
        print(f"❌ Dashboard: {e}")
        tests.append(("Dashboard", False))
    
    # Test 2: Real SLAM Viewer
    try:
        from real_slam_viewer import RealSLAMViewer
        print("✅ Viewer: RealSLAMViewer")
        tests.append(("Viewer", True))
    except Exception as e:
        print(f"❌ Viewer: {e}")
        tests.append(("Viewer", False))
    
    # Test 3: Integrated SLAM System
    try:
        from app.runtime.integrated_slam import IntegratedStereoSLAMSystem
        print("✅ SLAM: IntegratedStereoSLAMSystem")
        tests.append(("IntegratedSLAM", True))
    except Exception as e:
        print(f"❌ SLAM: {e}")
        tests.append(("IntegratedSLAM", False))
    
    # Test 4: Core SLAM
    try:
        from app.runtime.stereo_slam import StereoSLAMSystem
        print("✅ Core: StereoSLAMSystem")
        tests.append(("CoreSLAM", True))
    except Exception as e:
        print(f"❌ Core: {e}")
        tests.append(("CoreSLAM", False))
    
    # Test 5: Camera Handler
    try:
        from app.runtime.camera_stream_handler import StereoCameraManager
        print("✅ Camera: StereoCameraManager")
        tests.append(("CameraManager", True))
    except Exception as e:
        print(f"❌ Camera: {e}")
        tests.append(("CameraManager", False))
    
    # Test 6: Advanced Features
    try:
        from app.runtime.advanced_features import AdvancedFeatureExtractor
        print("✅ Features: AdvancedFeatureExtractor")
        tests.append(("Features", True))
    except Exception as e:
        print(f"❌ Features: {e}")
        tests.append(("Features", False))
    
    # Test 7: Visual Odometry
    try:
        from app.runtime.visual_odometry import VisualOdometryEngine
        print("✅ Odometry: VisualOdometryEngine")
        tests.append(("Odometry", True))
    except Exception as e:
        print(f"❌ Odometry: {e}")
        tests.append(("Odometry", False))
    
    # Summary
    print("\n" + "="*60)
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🔴 INTEGRATED SLAM SYSTEM READY!")
        print("\nTo start:")
        print("  python app/frontend/launch.py")
        print("\nThen click: 🎬 SLAM VIEWER")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        return False
    
    print("="*60 + "\n")

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
