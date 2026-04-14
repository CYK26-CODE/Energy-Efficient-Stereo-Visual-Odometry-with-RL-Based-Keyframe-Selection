"""
Stereo Vision Module
Handles stereo feature matching, depth estimation, and 3D point generation
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List

class StereoCalibratedPipeline:
    """
    Stereo vision pipeline with depth estimation
    """
    
    def __init__(self, frame_height: int = 480, frame_width: int = 640):
        """
        Initialize stereo vision pipeline
        
        Args:
            frame_height: Expected frame height
            frame_width: Expected frame width
        """
        self.frame_height = frame_height
        self.frame_width = frame_width
        
        # Initialize SIFT detector for feature matching
        self.sift = cv2.SIFT_create()
        
        # BFMatcher for feature matching
        self.bf_matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        
        # Stereo matcher for depth computation
        self.stereo_matcher = cv2.StereoBM_create(
            numDisparities=128,
            blockSize=15
        )
        
        # Assume approximate baseline (distance between cameras)
        # This should be calibrated for your specific camera setup
        self.baseline = 0.12  # 12cm baseline assumption
        self.focal_length = 500  # Estimated focal length in pixels
        
    def extract_features(self, frame: np.ndarray) -> Tuple[List, np.ndarray]:
        """
        Extract SIFT features from a frame
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of (keypoints, descriptors)
        """
        if frame is None or frame.size == 0:
            return [], np.array([])
        
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        keypoints, descriptors = self.sift.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray,
                      ratio_threshold: float = 0.7) -> List[Tuple[int, int]]:
        """
        Match features between two frames using Lowe's ratio test
        
        Args:
            desc1: Descriptors from first frame
            desc2: Descriptors from second frame
            ratio_threshold: Lowe's ratio test threshold
            
        Returns:
            List of matched feature indices
        """
        if desc1 is None or desc2 is None or len(desc1) == 0 or len(desc2) == 0:
            return []
        
        matches = self.bf_matcher.knnMatch(desc1, desc2, k=2)
        
        # Apply Lowe's ratio test to filter good matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append((m.queryIdx, m.trainIdx))
        
        return good_matches
    
    def estimate_depth_from_stereo(self, left_frame: np.ndarray,
                                  right_frame: np.ndarray) -> np.ndarray:
        """
        Estimate depth map from stereo pair using block matching
        
        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
            
        Returns:
            Depth map (disparity / focal_length * baseline)
        """
        # Convert to grayscale
        left_gray = cv2.cvtColor(left_frame, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_frame, cv2.COLOR_BGR2GRAY)
        
        # Compute disparity
        disparity = self.stereo_matcher.compute(left_gray, right_gray).astype(np.float32)
        
        # Avoid division by zero
        disparity[disparity <= 0] = 0.1
        
        # Convert disparity to depth: depth = (focal_length * baseline) / disparity
        depth = (self.focal_length * self.baseline) / (disparity / 16.0)
        
        return depth
    
    def compute_3d_points_from_matches(self, left_frame: np.ndarray,
                                      right_frame: np.ndarray,
                                      left_kp: List, right_kp: List,
                                      matches: List[Tuple[int, int]]) -> np.ndarray:
        """
        Compute 3D points from stereo matches
        
        Args:
            left_frame: Left camera frame
            right_frame: Right camera frame
            left_kp: Left frame keypoints
            right_kp: Right frame keypoints
            matches: Matched feature pairs
            
        Returns:
            Array of 3D points (Nx3)
        """
        if len(matches) == 0:
            return np.array([]).reshape(0, 3)
        
        # Estimate depth from stereo
        depth_map = self.estimate_depth_from_stereo(left_frame, right_frame)
        
        points_3d = []
        
        for match_idx_l, match_idx_r in matches:
            kp_left = left_kp[match_idx_l].pt
            kp_right = right_kp[match_idx_r].pt
            
            x_l, y_l = int(kp_left[0]), int(kp_left[1])
            
            # Bounds check
            if x_l < 0 or x_l >= depth_map.shape[1] or y_l < 0 or y_l >= depth_map.shape[0]:
                continue
            
            depth = depth_map[y_l, x_l]
            
            if depth > 0:
                # Simple triangulation (assuming calibrated cameras)
                # X = (x - cx) * depth / f
                # Y = (y - cy) * depth / f
                # Z = depth
                cx, cy = self.frame_width / 2, self.frame_height / 2
                
                X = (x_l - cx) * depth / self.focal_length
                Y = (y_l - cy) * depth / self.focal_length
                Z = depth
                
                points_3d.append([X, Y, Z])
        
        return np.array(points_3d) if points_3d else np.array([]).reshape(0, 3)
    
    def estimate_camera_motion(self, points_1: np.ndarray,
                              points_2: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Estimate camera rotation and translation from 3D point correspondences
        
        Args:
            points_1: 3D points from first frame
            points_2: 3D points from second frame (matched)
            
        Returns:
            Tuple of (rotation_matrix, translation_vector) or (None, None) if estimation fails
        """
        if len(points_1) < 4 or len(points_2) < 4:
            return None, None
        
        # Use Kabsch algorithm (SVD-based)
        # Compute centroids
        centroid_1 = np.mean(points_1, axis=0)
        centroid_2 = np.mean(points_2, axis=0)
        
        # Center the points
        points_1_centered = points_1 - centroid_1
        points_2_centered = points_2 - centroid_2
        
        # Compute covariance matrix
        H = points_1_centered.T @ points_2_centered
        
        # SVD
        U, S, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        
        # Ensure proper rotation matrix (det = 1)
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        
        # Compute translation
        t = centroid_2 - R @ centroid_1
        
        return R, t
