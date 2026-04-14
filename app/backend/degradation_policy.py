#!/usr/bin/env python3
"""
Graceful Degradation Module
Reduces map fidelity and computation as battery decreases
4 degradation levels based on battery percentage
"""

import numpy as np
from typing import Dict


class DegradationLevel:
    """Configuration for each degradation level"""
    
    def __init__(self, level: int, name: str, battery_threshold_low: float, 
                 battery_threshold_high: float):
        """
        Args:
            level: 0-3
            name: Human-readable name
            battery_threshold_low: Lower battery bound
            battery_threshold_high: Upper battery bound
        """
        self.level = level
        self.name = name
        self.battery_low = battery_threshold_low
        self.battery_high = battery_threshold_high
    
    def __repr__(self):
        return f"Level {self.level}: {self.name} ({self.battery_low:.0f}-{self.battery_high:.0f}%)"


class SLAMDegradationPolicy:
    """
    Manages graceful degradation of SLAM quality
    Based on battery level, reduces descriptor count, feature tracking, etc.
    """
    
    # Degradation levels
    LEVELS = [
        DegradationLevel(0, "FULL FIDELITY", 60, 100),
        DegradationLevel(1, "MILD DEGRADATION", 40, 60),
        DegradationLevel(2, "MODERATE DEGRADATION", 20, 40),
        DegradationLevel(3, "AGGRESSIVE/SAFE MODE", 0, 20)
    ]
    
    def __init__(self):
        """Initialize degradation policy"""
        self.current_level = 0
        self.current_battery = 100.0
        self.configuration = self._get_level_config(0)
    
    def update_battery(self, battery_pct: float) -> int:
        """
        Update battery level and return current degradation level
        
        Args:
            battery_pct: Battery percentage [0, 100]
            
        Returns:
            Current degradation level (0-3)
        """
        self.current_battery = battery_pct
        new_level = self._get_level_from_battery(battery_pct)
        
        if new_level != self.current_level:
            self.current_level = new_level
            self.configuration = self._get_level_config(new_level)
            return new_level
        
        return self.current_level
    
    def _get_level_from_battery(self, battery_pct: float) -> int:
        """Get degradation level from battery percentage"""
        if battery_pct >= 60:
            return 0
        elif battery_pct >= 40:
            return 1
        elif battery_pct >= 20:
            return 2
        else:
            return 3
    
    def _get_level_config(self, level: int) -> Dict:
        """
        Get configuration parameters for degradation level
        
        Args:
            level: 0-3
            
        Returns:
            Configuration dictionary
        """
        
        configs = {
            0: {  # Level 0: FULL FIDELITY (>= 60%)
                'name': 'FULL FIDELITY',
                'descriptor_retention': 1.0,          # Keep 100% of descriptors
                'descriptor_type': 'SIFT',             # Use expensive SIFT
                'keyframe_frequency': 1.0,             # Save all keyframes
                'loop_closure_frequency': 1.0,         # Check every frame
                'map_resolution': 'FINE',              # Fine-grained landmarks
                'bundle_adjustment_freq': 5,           # Frequent optimization
                'enable_imu_fusion': True,
                'enable_cloud_upload': True,
                'feature_quality_threshold': 0.01,     # Strict threshold
                'max_descriptor_count': 2000,          # Many descriptors
                'enable_dense_mapping': True,
                'optimization_iterations': 5
            },
            1: {  # Level 1: MILD DEGRADATION (40-60%)
                'name': 'MILD DEGRADATION',
                'descriptor_retention': 0.8,          # Keep 80% of descriptors
                'descriptor_type': 'SIFT',             # Still SIFT but selective
                'keyframe_frequency': 0.9,             # Skip 10% of frames
                'loop_closure_frequency': 0.9,         # Check 90% as often
                'map_resolution': 'MEDIUM',            # Medium-grained landmarks
                'bundle_adjustment_freq': 8,           # Less frequent
                'enable_imu_fusion': True,
                'enable_cloud_upload': True,
                'feature_quality_threshold': 0.02,
                'max_descriptor_count': 1500,
                'enable_dense_mapping': True,
                'optimization_iterations': 3
            },
            2: {  # Level 2: MODERATE DEGRADATION (20-40%)
                'name': 'MODERATE DEGRADATION',
                'descriptor_retention': 0.5,          # Keep 50% of descriptors
                'descriptor_type': 'ORB',              # Switch to fast ORB
                'keyframe_frequency': 0.7,             # Skip 30% of frames
                'loop_closure_frequency': 0.5,         # Check half as often
                'map_resolution': 'COARSE',            # Coarse landmarks
                'bundle_adjustment_freq': 15,          # Infrequent
                'enable_imu_fusion': False,            # Disable IMU
                'enable_cloud_upload': False,          # Stop uploads
                'feature_quality_threshold': 0.05,
                'max_descriptor_count': 800,
                'enable_dense_mapping': False,
                'optimization_iterations': 1
            },
            3: {  # Level 3: AGGRESSIVE/SAFE MODE (< 20%)
                'name': 'AGGRESSIVE/SAFE MODE',
                'descriptor_retention': 0.2,          # Keep only 20% of descriptors
                'descriptor_type': 'FAST',             # Cheapest features (FAST)
                'keyframe_frequency': 0.4,             # Skip 60% of frames
                'loop_closure_frequency': 0.1,         # Minimal loop closure
                'map_resolution': 'VERY_COARSE',       # Sparse landmarks
                'bundle_adjustment_freq': 100,         # Almost never
                'enable_imu_fusion': False,
                'enable_cloud_upload': False,
                'feature_quality_threshold': 0.1,
                'max_descriptor_count': 300,
                'enable_dense_mapping': False,
                'optimization_iterations': 0
            }
        }
        
        return configs.get(level, configs[0])
    
    def should_create_keyframe(self, random_value: float = None) -> bool:
        """
        Determine if keyframe should be created based on degradation level
        Uses stochastic decision based on keyframe_frequency
        
        Args:
            random_value: Optional random value for determinism
            
        Returns:
            True if keyframe should be created
        """
        if random_value is None:
            random_value = np.random.random()
        
        threshold = self.configuration['keyframe_frequency']
        return random_value < threshold
    
    def should_check_loop_closure(self, frame_count: int) -> bool:
        """
        Determine if loop closure should be checked
        
        Args:
            frame_count: Current frame count
            
        Returns:
            True if check should be performed
        """
        freq = self.configuration['loop_closure_frequency']
        
        if freq >= 0.99:
            return True  # Check every frame
        elif freq >= 0.5:
            return frame_count % 2 == 0  # Check every other frame
        elif freq >= 0.2:
            return frame_count % 5 == 0  # Check every 5 frames
        else:
            return frame_count % 10 == 0  # Check every 10 frames
    
    def get_max_descriptors(self) -> int:
        """Get max descriptor count for current level"""
        return self.configuration['max_descriptor_count']
    
    def get_descriptor_type(self) -> str:
        """Get descriptor type (SIFT, ORB, FAST) for current level"""
        return self.configuration['descriptor_type']
    
    def get_feature_quality_threshold(self) -> float:
        """Get feature quality threshold (higher = stricter)"""
        return self.configuration['feature_quality_threshold']
    
    def should_run_bundle_adjustment(self, keyframe_count: int) -> bool:
        """
        Determine if bundle adjustment should run
        
        Args:
            keyframe_count: Current keyframe count
            
        Returns:
            True if optimization should run
        """
        freq = self.configuration['bundle_adjustment_freq']
        return keyframe_count % freq == 0 and keyframe_count > 0
    
    def get_optimization_iterations(self) -> int:
        """Get number of bundle adjustment iterations"""
        return self.configuration['optimization_iterations']
    
    def subsample_descriptors(self, descriptors: np.ndarray) -> np.ndarray:
        """
        Subsample descriptor set based on retention rate
        Keeps the most informative descriptors
        
        Args:
            descriptors: [N, D] descriptor matrix
            
        Returns:
            Subsampled descriptors
        """
        if len(descriptors) == 0:
            return descriptors
        
        retention = self.configuration['descriptor_retention']
        
        if retention >= 0.99:
            return descriptors
        
        # Keep most informative descriptors (highest variance)
        keep_count = max(1, int(len(descriptors) * retention))
        
        # Sort by variance across descriptor dimensions
        descriptor_variance = np.var(descriptors, axis=1)
        top_indices = np.argsort(descriptor_variance)[-keep_count:]
        
        return descriptors[top_indices]
    
    def get_status(self) -> Dict:
        """Get detailed degradation status"""
        return {
            'level': self.current_level,
            'name': self.configuration['name'],
            'battery_pct': self.current_battery,
            'descriptor_type': self.get_descriptor_type(),
            'max_descriptors': self.get_max_descriptors(),
            'keyframe_frequency': self.configuration['keyframe_frequency'],
            'loop_closure_frequency': self.configuration['loop_closure_frequency'],
            'enable_imu': self.configuration['enable_imu_fusion'],
            'enable_cloud': self.configuration['enable_cloud_upload'],
            'enable_dense': self.configuration['enable_dense_mapping']
        }
    
    def print_status(self):
        """Print current degradation status"""
        status = self.get_status()
        print(f"\n{'=' * 70}")
        print(f"🔋 SLAM DEGRADATION STATUS")
        print(f"{'=' * 70}")
        print(f"Battery: {status['battery_pct']:.1f}%")
        print(f"Degradation Level: {status['level']} - {status['name']}")
        print(f"\nConfiguration:")
        print(f"  • Descriptor Type: {status['descriptor_type']}")
        print(f"  • Max Descriptors: {status['max_descriptors']}")
        print(f"  • Keyframe Frequency: {status['keyframe_frequency']:.0%}")
        print(f"  • Loop Closure Frequency: {status['loop_closure_frequency']:.0%}")
        print(f"  • IMU Fusion: {'ENABLED' if status['enable_imu'] else 'DISABLED'}")
        print(f"  • Cloud Upload: {'ENABLED' if status['enable_cloud'] else 'DISABLED'}")
        print(f"  • Dense Mapping: {'ENABLED' if status['enable_dense'] else 'DISABLED'}")
        print(f"{'=' * 70}\n")
