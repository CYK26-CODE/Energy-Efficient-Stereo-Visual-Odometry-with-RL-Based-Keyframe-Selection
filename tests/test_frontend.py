#!/usr/bin/env python3
"""Test script to verify frontend components load correctly"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app' / 'frontend'))
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))

print("Testing Frontend Components...\n")

try:
    print("1. Testing main_dashboard import...", end=" ")
    from main_dashboard import AdvancedDQNTrainingDashboard
    print("✅")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

try:
    print("2. Testing backend_interface import...", end=" ")
    from backend_interface import BackendInterface, ConfigurationManager
    print("✅")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

try:
    print("3. Testing reward_configurator import...", end=" ")
    from reward_configurator import RewardConfigurator
    print("✅")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

try:
    print("4. Testing degradation_configurator import...", end=" ")
    from degradation_configurator import BatteryDegradationConfigurator
    print("✅")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

try:
    print("5. Testing metrics_visualizer import...", end=" ")
    from metrics_visualizer import RealtimeMetricsDisplay
    print("✅")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n✅ All frontend components loaded successfully!")
print("\nYou can now run: python app/frontend/launch.py")
