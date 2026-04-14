"""
Visual Odometry Engine
Tracks camera motion and builds 3D point cloud with trajectory
"""

import numpy as np
import cv2
from collections import deque
from typing import Optional, Tuple, List
from stereo_vision import StereoCalibratedPipeline

class VisualOdometryEngine:
    """
    Visual odometry engine that tracks camera motion over time
    """
    
    def __init__(self, max_trajectory_points: int = 1000):
        """
        Initialize visual odometry engine
        
        Args:
            max_trajectory_points: Maximum number of trajectory points to store
        """
        self.stereo_pipeline = StereoCalibratedPipeline()
        
        # Camera pose (transformation matrix)
        self.camera_pose = np.eye(4)  # 4x4 identity matrix
        
        # Trajectory storage
        self.trajectory = deque(maxlen=max_trajectory_points)
        self.trajectory_poses = deque(maxlen=max_trajectory_points)
        
        # 3D point cloud
        self.point_cloud = np.array([]).reshape(0, 3)
        self.point_cloud_colors = np.array([]).reshape(0, 3)
        
        # Previous frame data
        self.prev_keypoints = None
        self.prev_descriptors = None
        self.prev_frame = None
        
        # Frame counter
        self.frame_count = 0
        
    def process_stereo_pair(self, left_frame: np.ndarray,
                           right_frame: np.ndarray) -> bool:
        """
        Process a stereo frame pair and update odometry
        
        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
            
        Returns:
            True if successful, False otherwise
        """
        self.frame_count += 1
        
        # Extract features from left frame
        keypoints, descriptors = self.stereo_pipeline.extract_features(left_frame)
        
        if len(keypoints) < 8:
            print(f"Frame {self.frame_count}: Not enough features detected")
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.prev_frame = left_frame
            return False
        
        # First frame: initialize
        if self.prev_keypoints is None:
            print(f"Frame {self.frame_count}: Initializing with stereo baseline")
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.prev_frame = left_frame
            
            # Compute initial 3D points from stereo
            self._initialize_point_cloud(left_frame, right_frame, keypoints, descriptors)
            
            # Store initial pose
            self._add_trajectory_point()
            return True
        
        # Subsequent frames: estimate motion
        # Match features between current and previous frame (within left camera)
        matches = self.stereo_pipeline.match_features(descriptors, self.prev_descriptors)
        
        if len(matches) < 4:
            print(f"Frame {self.frame_count}: Not enough feature matches")
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.prev_frame = left_frame
            return False
        
        # Extract matched points
        current_pts = np.float32([keypoints[m[0]].pt for m in matches])
        prev_pts = np.float32([self.prev_keypoints[m[1]].pt for m in matches])
        
        # Estimate essential matrix for motion estimation
        try:
            E, mask = cv2.findEssentialMat(current_pts, prev_pts, 
                                           focal=self.stereo_pipeline.focal_length,
                                           pp=(self.stereo_pipeline.frame_width/2,
                                               self.stereo_pipeline.frame_height/2),
                                           method=cv2.RANSAC, prob=0.999, threshold=1.0)
            
            if E is None or mask is None:
                print(f"Frame {self.frame_count}: Could not compute essential matrix")
                self.prev_keypoints = keypoints
                self.prev_descriptors = descriptors
                self.prev_frame = left_frame
                return False
            
            # Filter matches using mask
            good_matches = mask.ravel().astype(bool)
            good_current_pts = current_pts[good_matches]
            good_prev_pts = prev_pts[good_matches]
            
            # Check if we have enough good points
            if len(good_current_pts) < 5:
                print(f"Frame {self.frame_count}: Not enough inliers after RANSAC")
                self.prev_keypoints = keypoints
                self.prev_descriptors = descriptors
                self.prev_frame = left_frame
                return False
            
            # Recover pose from essential matrix
            _, R, t, pose_mask = cv2.recoverPose(E, good_current_pts, good_prev_pts,
                                           focal=self.stereo_pipeline.focal_length,
                                           pp=(self.stereo_pipeline.frame_width/2,
                                               self.stereo_pipeline.frame_height/2))
            
            # Update camera pose
            self._update_camera_pose(R, t)
            
            # Add trajectory point
            self._add_trajectory_point()
            
            # Update point cloud
            self._update_point_cloud(left_frame, right_frame, keypoints, descriptors)
            
            print(f"Frame {self.frame_count}: Motion estimated - Translation: {np.linalg.norm(t):.4f}")
            
        except Exception as e:
            print(f"Frame {self.frame_count}: Error in pose estimation - {str(e)}")
            return False
        finally:
            # Store current frame data for next iteration
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.prev_frame = left_frame
        
        return True
    
    def _initialize_point_cloud(self, left_frame: np.ndarray,
                               right_frame: np.ndarray,
                               keypoints: List, descriptors: np.ndarray):
        """
        Initialize point cloud from stereo pair
        
        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
            keypoints: Keypoints from left frame
            descriptors: Descriptors from left frame
        """
        # Extract features from right frame
        right_kp, right_desc = self.stereo_pipeline.extract_features(right_frame)
        
        # Match features between left and right
        matches = self.stereo_pipeline.match_features(descriptors, right_desc)
        
        # Compute 3D points
        points_3d = self.stereo_pipeline.compute_3d_points_from_matches(
            left_frame, right_frame, keypoints, right_kp, matches
        )
        
        if len(points_3d) > 0:
            # Sample colors from left frame
            colors = self._sample_colors(left_frame, keypoints, matches, descriptors)
            
            self.point_cloud = points_3d
            self.point_cloud_colors = colors
            print(f"Initialized point cloud with {len(points_3d)} points")
    
    def _update_point_cloud(self, left_frame: np.ndarray,
                           right_frame: np.ndarray,
                           keypoints: List, descriptors: np.ndarray):
        """
        Update point cloud with new 3D points
        
        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
            keypoints: Keypoints from left frame
            descriptors: Descriptors from left frame
        """
        # Extract features from right frame
        right_kp, right_desc = self.stereo_pipeline.extract_features(right_frame)
        
        # Match features between left and right
        matches = self.stereo_pipeline.match_features(descriptors, right_desc)
        
        # Compute 3D points
        points_3d = self.stereo_pipeline.compute_3d_points_from_matches(
            left_frame, right_frame, keypoints, right_kp, matches
        )
        
        if len(points_3d) > 0:
            # Sample colors
            colors = self._sample_colors(left_frame, keypoints, matches, descriptors)
            
            # Transform to world coordinates
            points_3d_world = self._transform_to_world(points_3d)
            
            # Add to point cloud
            self.point_cloud = np.vstack([self.point_cloud, points_3d_world])
            self.point_cloud_colors = np.vstack([self.point_cloud_colors, colors])
            
            print(f"Point cloud updated to {len(self.point_cloud)} points")
    
    def _sample_colors(self, frame: np.ndarray, keypoints: List,
                      matches: List[Tuple[int, int]], descriptors: np.ndarray) -> np.ndarray:
        """
        Sample colors from frame at keypoint locations
        
        Args:
            frame: Input frame
            keypoints: Keypoints
            matches: Matched pairs (only used for indexing)
            descriptors: Feature descriptors
            
        Returns:
            RGB colors for matched points
        """
        if len(matches) == 0:
            return np.array([]).reshape(0, 3)
        
        colors = []
        for match_idx_l, _ in matches[:min(len(matches), len(keypoints))]:
            if match_idx_l < len(keypoints):
                x, y = int(keypoints[match_idx_l].pt[0]), int(keypoints[match_idx_l].pt[1])
                
                # Bounds check
                if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
                    bgr = frame[y, x]
                    rgb = [bgr[2], bgr[1], bgr[0]]  # Convert BGR to RGB
                    colors.append(rgb)
        
        return np.array(colors) if colors else np.array([]).reshape(0, 3)
    
    def _update_camera_pose(self, R: np.ndarray, t: np.ndarray):
        """
        Update camera pose with new rotation and translation
        
        Args:
            R: Rotation matrix
            t: Translation vector
        """
        # Create transformation matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t.flatten()
        
        # Update camera pose
        self.camera_pose = self.camera_pose @ T
    
    def _add_trajectory_point(self):
        """Add current camera center to trajectory"""
        # Extract camera center from pose matrix
        # Camera center in world coordinates: -R^T @ t
        pose = self.camera_pose
        
        # Camera position is the negative translation part (when pose is [R|t])
        camera_center = pose[:3, 3]
        
        self.trajectory.append(camera_center)
        self.trajectory_poses.append(self.camera_pose.copy())
    
    def _transform_to_world(self, points_3d: np.ndarray) -> np.ndarray:
        """
        Transform 3D points from camera coordinates to world coordinates
        
        Args:
            points_3d: Points in camera coordinates (Nx3)
            
        Returns:
            Points in world coordinates (Nx3)
        """
        if len(points_3d) == 0:
            return points_3d
        
        # Apply camera pose transformation
        R = self.camera_pose[:3, :3]
        t = self.camera_pose[:3, 3]
        
        points_world = (R @ points_3d.T).T + t
        return points_world
    
    def get_trajectory(self) -> np.ndarray:
        """Get camera trajectory as array of positions"""
        if len(self.trajectory) == 0:
            return np.array([]).reshape(0, 3)
        return np.array(list(self.trajectory))
    
    def get_point_cloud(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get point cloud and colors
        
        Returns:
            Tuple of (points, colors)
        """
        return self.point_cloud, self.point_cloud_colors
    
    def get_camera_pose(self) -> np.ndarray:
        """Get current camera pose (4x4 transformation matrix)"""
        return self.camera_pose.copy()
