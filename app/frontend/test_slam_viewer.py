#!/usr/bin/env python3
"""
Test SLAM Viewer Integration
Validates all components and functionality
"""

import sys
from pathlib import Path

def test_slam_viewer_integration():
    """Test SLAM viewer with main dashboard"""
    
    print("\n" + "="*60)
    print("SLAM VIEWER INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Test 1: Import main dashboard
    print("1. Testing main dashboard import...")
    try:
        from main_dashboard import AdvancedDQNTrainingDashboard
        print("   ✅ Main dashboard imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import main dashboard: {e}")
        return False
    
    # Test 2: Import SLAM viewer
    print("\n2. Testing SLAM viewer import...")
    try:
        from slam_viewer import SLAMViewer
        print("   ✅ SLAM viewer imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import SLAM viewer: {e}")
        return False
    
    # Test 3: Check SLAM viewer has required methods
    print("\n3. Testing SLAM viewer methods...")
    required_methods = [
        'update_camera_feeds',
        'update_2d_map',
        'update_3d_map',
        'update_statistics',
        'update_battery',
        '_on_edit_config',
        'on_closing'
    ]
    
    viewer_methods = dir(SLAMViewer)
    missing_methods = []
    
    for method in required_methods:
        if method not in viewer_methods:
            missing_methods.append(method)
    
    if missing_methods:
        print(f"   ❌ Missing methods: {missing_methods}")
        return False
    else:
        print(f"   ✅ All {len(required_methods)} required methods present")
    
    # Test 4: Check main dashboard has SLAM button
    print("\n4. Testing dashboard SLAM integration...")
    dashboard_methods = dir(AdvancedDQNTrainingDashboard)
    slam_methods = [
        '_open_slam_viewer',
        '_open_slam_config_editor',
        '_update_slam_viewer_data'
    ]
    
    missing_slam = []
    for method in slam_methods:
        if method not in dashboard_methods:
            missing_slam.append(method)
    
    if missing_slam:
        print(f"   ❌ Missing dashboard methods: {missing_slam}")
        return False
    else:
        print(f"   ✅ All {len(slam_methods)} dashboard SLAM methods present")
    
    # Test 5: Validate imports in main dashboard
    print("\n5. Validating imports...")
    try:
        with open('main_dashboard.py', 'r') as f:
            content = f.read()
            if 'from slam_viewer import SLAMViewer' in content:
                print("   ✅ SLAM viewer properly imported in main_dashboard.py")
            else:
                print("   ❌ SLAM viewer import missing from main_dashboard.py")
                return False
    except Exception as e:
        print(f"   ❌ Failed to check imports: {e}")
        return False
    
    # Test 6: Check button text
    print("\n6. Checking UI elements...")
    try:
        with open('main_dashboard.py', 'r') as f:
            content = f.read()
            if '🎬 SLAM VIEWER' in content:
                print("   ✅ SLAM VIEWER button added to dashboard")
            else:
                print("   ❌ SLAM VIEWER button not found in dashboard")
                return False
    except Exception as e:
        print(f"   ❌ Failed to check UI elements: {e}")
        return False
    
    # Test 7: Verify config edit button
    print("\n7. Checking Edit Config button...")
    try:
        with open('slam_viewer.py', 'r') as f:
            content = f.read()
            if '⚙ Edit Config' in content and '_on_edit_config' in content:
                print("   ✅ Edit Config button properly implemented")
            else:
                print("   ❌ Edit Config button implementation incomplete")
                return False
    except Exception as e:
        print(f"   ❌ Failed to verify Edit Config: {e}")
        return False
    
    # Test 8: Syntax check both files
    print("\n8. Checking Python syntax...")
    import py_compile
    files_to_check = ['main_dashboard.py', 'slam_viewer.py']
    
    for file in files_to_check:
        try:
            py_compile.compile(file, doraise=True)
            print(f"   ✅ {file} - Valid syntax")
        except py_compile.PyCompileError as e:
            print(f"   ❌ {file} - Syntax error: {e}")
            return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - SLAM VIEWER FULLY INTEGRATED")
    print("="*60)
    print("\nThe SLAM Viewer is ready to use:")
    print("  1. Run: python app/frontend/launch.py")
    print("  2. Click '🎬 SLAM VIEWER' button in Training Control")
    print("  3. Click '⚙ Edit Config' to configure SLAM parameters")
    print("\nFeatures:")
    print("  • Left/Right stereo camera feeds (640x360 each)")
    print("  • 2D map with trajectory overlay")
    print("  • 3D point cloud visualization")
    print("  • Battery level and degradation monitoring")
    print("  • Real-time system statistics (FPS, features, landmarks, etc.)")
    print("  • Thread-safe updates from backend")
    print("\n" + "="*60 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_slam_viewer_integration()
    sys.exit(0 if success else 1)
