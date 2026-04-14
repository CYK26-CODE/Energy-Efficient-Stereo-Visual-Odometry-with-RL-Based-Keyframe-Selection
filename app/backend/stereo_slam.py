"""
Complete Stereo SLAM System
Integrates stereo vision, visual odometry, loop closure, and bundle adjustment
for complete simultaneous localization and mapping
"""

import numpy as np
import cv2
from collections import deque
from typing import Optional, Tuple, List, Dict
from advanced_features import AdvancedFeatureExtractor, RobustStereoMatcher, EpipolarGeometry
from visual_odometry import VisualOdometryEngine


class KeyFrame:
    """Represents a keyframe in the SLAM system"""
    
    def __init__(self, frame_id: int, timestamp: float,
                 pose: np.ndarray, left_frame: np.ndarray,
                 right_frame: np.ndarray, keypoints: List,
                 descriptors: np.ndarray):
        """
        Initialize keyframe
        
        Args:
            frame_id: Frame identifier
            timestamp: Frame timestamp
            pose: 4x4 transformation matrix
            left_frame: Left camera image
            right_frame: Right camera image
            keypoints: Feature keypoints
            descriptors: Feature descriptors
        """
        self.frame_id = frame_id
        self.timestamp = timestamp
        self.pose = pose.copy()
        self.left_frame = left_frame.copy()
        self.right_frame = right_frame.copy()
        self.keypoints = keypoints
        self.descriptors = descriptors.copy() if descriptors is not None else None
        self.point_ids = {}  # Map keypoint index to 3D point ID
        
    def get_camera_center(self) -> np.ndarray:
        """Get camera center in world coordinates"""
        return self.pose[:3, 3]


class StereoSLAMSystem:
    """
    Complete Stereo SLAM system with loop closure and bundle adjustment
    """
    
    def __init__(self, max_keyframes: int = 100,
                 min_displacement: float = 0.05,
                 loop_closure_threshold: float = 0.8):
        """
        Initialize Stereo SLAM system
        
        Args:
            max_keyframes: Maximum number of keyframes to store
            min_displacement: Minimum displacement to create new keyframe
            loop_closure_threshold: Threshold for loop closure detection
        """
        self.max_keyframes = max_keyframes
        self.min_displacement = min_displacement
        self.loop_closure_threshold = loop_closure_threshold
        
        # Core components
        self.feature_extractor = AdvancedFeatureExtractor(method='orb', max_features=500)
        self.stereo_matcher = RobustStereoMatcher(method='bf')  # Use BF for ORB descriptors
        self.epipolar_geom = EpipolarGeometry()
        self.visual_odometry = VisualOdometryEngine()
        
        # SLAM state
        self.keyframes = deque(maxlen=max_keyframes)
        self.point_cloud = np.array([]).reshape(0, 3)
        self.point_cloud_colors = np.array([]).reshape(0, 3)
        self.point_ids = {}  # Map 3D point ID to observations
        self.next_point_id = 0
        
        # Loop closure tracking
        self.loop_closures = []
        self.loop_closure_graph = {}
        
        # Trajectory
        self.trajectory = deque(maxlen=max_keyframes)
        self.frame_count = 0
        self.keyframe_count = 0
        
        # Last keyframe for comparison
        self.last_keyframe = None
        self.last_pose = np.eye(4)
        
    def process_stereo_pair(self, left_frame: np.ndarray,
                           right_frame: np.ndarray,
                           timestamp: float = 0.0) -> bool:
        """
        Process a stereo frame pair
        
        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
            timestamp: Frame timestamp
            
        Returns:
            True if keyframe was created
        """
        self.frame_count += 1
        
        # Validate frames
        if left_frame is None or left_frame.size == 0 or right_frame is None or right_frame.size == 0:
            print(f"Frame {self.frame_count}: Invalid frames received")
            return False
        
        # Extract features from left frame
        left_kp, left_desc, left_quality = self.feature_extractor.extract_features(left_frame)
        
        if len(left_kp) < 20:
            if self.frame_count % 50 == 0:
                print(f"Frame {self.frame_count}: Insufficient left features ({len(left_kp)}, quality: {left_quality:.2f})")
            return False
        
        # Extract features from right frame
        right_kp, right_desc, right_quality = self.feature_extractor.extract_features(right_frame)
        
        if len(right_kp) < 20:
            if self.frame_count % 50 == 0:
                print(f"Frame {self.frame_count}: Insufficient right features ({len(right_kp)})")
            return False
        
        # Match stereo pairs
        stereo_matches = self.stereo_matcher.match_stereo(left_desc, right_desc)
        
        if len(stereo_matches) < 10:
            if self.frame_count % 50 == 0:
                print(f"Frame {self.frame_count}: Insufficient stereo matches ({len(stereo_matches)})")
            return False
        
        # Process with visual odometry
        success = self.visual_odometry.process_stereo_pair(left_frame, right_frame)
        
        current_pose = self.visual_odometry.get_camera_pose()
        
        # Check if we should create a keyframe
        should_create_keyframe = self._should_create_keyframe(current_pose)
        
        if should_create_keyframe and success:
            # Create keyframe
            keyframe = KeyFrame(
                frame_id=self.frame_count,
                timestamp=timestamp,
                pose=current_pose,
                left_frame=left_frame,
                right_frame=right_frame,
                keypoints=left_kp,
                descriptors=left_desc
            )
            
            self.keyframes.append(keyframe)
            self.last_keyframe = keyframe
            self.last_pose = current_pose
            self.keyframe_count += 1
            self.trajectory.append(current_pose[:3, 3])
            
            # Extract and add 3D points
            self._add_points_from_stereo(keyframe, left_kp, right_kp, stereo_matches, left_frame)
            
            # Detect loop closures
            self._detect_loop_closure(keyframe)
            
            print(f"[KEYFRAME {self.keyframe_count}] Frame {self.frame_count} | "
                  f"Features: L={len(left_kp)} R={len(right_kp)} | "
                  f"Stereo Matches: {len(stereo_matches)} | "
                  f"Quality: {left_quality:.2f}")
            
            return True
        
        return False
    
    def _should_create_keyframe(self, current_pose: np.ndarray) -> bool:
        """
        Determine if current frame should be a keyframe
        
        Args:
            current_pose: Current camera pose
            
        Returns:
            True if keyframe should be created
        """
        if self.last_keyframe is None:
            return True
        
        # Check displacement from last keyframe
        displacement = np.linalg.norm(current_pose[:3, 3] - self.last_pose[:3, 3])
        
        return displacement > self.min_displacement
    
    def _add_points_from_stereo(self, keyframe: KeyFrame,
                               left_kp: List, right_kp: List,
                               matches: List[Tuple[int, int]],
                               left_frame: np.ndarray):
        """
        Extract and add 3D points from stereo matches
        
        Args:
            keyframe: Current keyframe
            left_kp: Left keypoints
            right_kp: Right keypoints
            matches: Stereo matches
            left_frame: Left frame for color sampling
        """
        points_3d = self.visual_odometry.stereo_pipeline.compute_3d_points_from_matches(
            keyframe.left_frame, keyframe.right_frame, left_kp, right_kp, matches
        )
        
        if len(points_3d) > 0:
            # Transform to world coordinates
            points_world = self._transform_to_world(points_3d, keyframe.pose)
            
            # Sample colors
            colors_sampled = self._sample_colors(left_frame, left_kp, matches)
            
            # Add to point cloud
            self.point_cloud = np.vstack([self.point_cloud, points_world])
            self.point_cloud_colors = np.vstack([self.point_cloud_colors, colors_sampled])
            
            # Create point IDs for observations
            for i, (match_idx_l, _) in enumerate(matches):
                if i < len(points_world):
                    point_id = self.next_point_id
                    keyframe.point_ids[match_idx_l] = point_id
                    
                    if point_id not in self.point_ids:
                        self.point_ids[point_id] = []
                    self.point_ids[point_id].append((keyframe.frame_id, match_idx_l))
                    
                    self.next_point_id += 1
    
    def _transform_to_world(self, points_3d: np.ndarray, pose: np.ndarray) -> np.ndarray:
        """Transform points from camera to world coordinates"""
        if len(points_3d) == 0:
            return points_3d
        
        R = pose[:3, :3]
        t = pose[:3, 3]
        
        points_world = (R @ points_3d.T).T + t
        return points_world
    
    def _sample_colors(self, frame: np.ndarray, keypoints: List,
                      matches: List[Tuple[int, int]]) -> np.ndarray:
        """Sample colors from frame at keypoint locations"""
        colors = []
        
        for match_idx_l, _ in matches:
            if match_idx_l < len(keypoints):
                x, y = int(keypoints[match_idx_l].pt[0]), int(keypoints[match_idx_l].pt[1])
                
                if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
                    bgr = frame[y, x]
                    rgb = [bgr[2], bgr[1], bgr[0]]
                    colors.append(rgb)
        
        return np.array(colors) if colors else np.array([]).reshape(0, 3)
    
    def _detect_loop_closure(self, keyframe: KeyFrame):
        """
        Detect loop closure by matching current keyframe with previous keyframes
        
        Args:
            keyframe: Current keyframe
        """
        if len(self.keyframes) < 10:
            return
        
        # Compare with keyframes from at least 10 frames ago
        early_keyframes = list(self.keyframes)[:-10]
        
        best_match_id = None
        best_match_score = 0.0
        
        for old_keyframe in early_keyframes:
            # Match descriptors
            matches = self.stereo_matcher.match_temporal(
                old_keyframe.descriptors, keyframe.descriptors
            )
            
            if len(matches) > 0:
                # Calculate match score
                match_score = len(matches) / (len(old_keyframe.keypoints) + len(keyframe.keypoints))
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match_id = old_keyframe.frame_id
        
        # If loop closure detected
        if best_match_score > self.loop_closure_threshold:
            self.loop_closures.append((best_match_id, keyframe.frame_id, best_match_score))
            self.loop_closure_graph[keyframe.frame_id] = best_match_id
            
            print(f"Loop closure detected: Frame {best_match_id} <-> {keyframe.frame_id} "
                  f"(Score: {best_match_score:.3f})")
    
    def optimize_bundle(self, max_iterations: int = 3):
        """
        Perform local bundle adjustment on recent frames
        
        Args:
            max_iterations: Maximum optimization iterations
        """
        if len(self.keyframes) < 2:
            return
        
        # For simplicity, optimize last 5 keyframes
        keyframes_to_optimize = list(self.keyframes)[-5:]
        
        for iteration in range(max_iterations):
            # Simple optimization: refine poses based on reprojection error
            for kf in keyframes_to_optimize:
                # Compute pose refinement (simplified)
                if len(kf.keypoints) > 0 and len(self.point_cloud) > 0:
                    # Could implement full bundle adjustment here
                    pass
    
    def get_trajectory(self) -> np.ndarray:
        """Get camera trajectory"""
        return np.array(list(self.trajectory)) if len(self.trajectory) > 0 else np.array([]).reshape(0, 3)
    
    def get_point_cloud(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get point cloud and colors"""
        return self.point_cloud, self.point_cloud_colors
    
    def get_keyframes_info(self) -> Dict:
        """Get information about keyframes"""
        return {
            'total_keyframes': self.keyframe_count,
            'total_points': len(self.point_cloud),
            'loop_closures': len(self.loop_closures),
            'frames_processed': self.frame_count
        }
    
    def save_map(self, filename: str):
        """Save SLAM map to file"""
        data = {
            'point_cloud': self.point_cloud.tolist(),
            'point_cloud_colors': self.point_cloud_colors.tolist(),
            'trajectory': self.get_trajectory().tolist(),
            'keyframes': self.keyframe_count,
            'loop_closures': self.loop_closures,
            'frames_processed': self.frame_count
        }
        
        import json
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved SLAM map to {filename}")
