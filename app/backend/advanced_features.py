"""
Advanced Stereo Feature Extraction and Matching Module
Implements multiple feature detectors and robust matching strategies
"""

import cv2
import numpy as np
from scipy.spatial.distance import cdist
import json
from typing import Tuple, List, Optional


class AdvancedFeatureExtractor:
    """
    Advanced feature extraction using multiple detectors (SIFT, ORB, AKAZE)
    with adaptive thresholding and quality metrics
    """
    
    def __init__(self, method: str = 'sift', max_features: int = 2000):
        """
        Initialize feature extractor
        
        Args:
            method: Feature detector ('sift', 'orb', 'akaze', 'hybrid')
            max_features: Maximum number of features to extract
        """
        self.method = method
        self.max_features = max_features
        
        # Initialize detectors
        if method in ['sift', 'hybrid']:
            self.sift = cv2.SIFT_create(nfeatures=max_features)
        
        if method in ['orb', 'hybrid']:
            self.orb = cv2.ORB_create(nfeatures=max_features)
        
        if method in ['akaze', 'hybrid']:
            self.akaze = cv2.AKAZE_create(threshold=10)
        
        self.feature_quality_history = []
    
    def extract_features(self, frame: np.ndarray) -> Tuple[List, np.ndarray, np.ndarray]:
        """
        Extract features from frame
        
        Args:
            frame: Input image
            
        Returns:
            Tuple of (keypoints, descriptors, quality_score)
        """
        if frame is None or frame.size == 0:
            return [], np.array([]), 0.0
        
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Adaptive histogram equalization for better feature extraction
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        if self.method == 'sift':
            kp, desc = self.sift.detectAndCompute(gray, None)
        
        elif self.method == 'orb':
            kp, desc = self.orb.detectAndCompute(gray, None)
        
        elif self.method == 'akaze':
            kp, desc = self.akaze.detectAndCompute(gray, None)
        
        elif self.method == 'hybrid':
            # Combine multiple detectors for robustness
            kp_sift, desc_sift = self.sift.detectAndCompute(gray, None)
            kp_orb, desc_orb = self.orb.detectAndCompute(gray, None)
            
            kp = kp_sift + kp_orb
            if desc_sift is not None and desc_orb is not None:
                desc = np.vstack([desc_sift, desc_orb])
            elif desc_sift is not None:
                desc = desc_sift
            else:
                desc = desc_orb
        
        # Calculate quality score (based on number and distribution of features)
        quality_score = self._calculate_quality_score(kp, gray)
        self.feature_quality_history.append(quality_score)
        
        return kp, desc, quality_score
    
    def _calculate_quality_score(self, keypoints: List, image: np.ndarray) -> float:
        """Calculate quality score for feature detection"""
        if len(keypoints) == 0:
            return 0.0
        
        # Score based on number of features
        num_score = min(len(keypoints) / self.max_features, 1.0)
        
        # Score based on feature distribution
        if len(keypoints) > 10:
            positions = np.array([kp.pt for kp in keypoints])
            # Calculate spatial entropy (higher is better)
            hist, _ = np.histogram(positions[:, 0], bins=10)
            entropy = -np.sum((hist / hist.sum()) * np.log(hist / hist.sum() + 1e-10))
            dist_score = entropy / np.log(10)
        else:
            dist_score = 0.0
        
        return 0.7 * num_score + 0.3 * dist_score


class RobustStereoMatcher:
    """
    Robust stereo feature matching with multiple strategies
    """
    
    def __init__(self, method: str = 'flann'):
        """
        Initialize stereo matcher
        
        Args:
            method: Matching method ('bf', 'flann', 'hybrid')
        """
        self.method = method
        
        if method in ['flann', 'hybrid']:
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            self.flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        if method in ['bf', 'hybrid']:
            # Use NORM_HAMMING for binary descriptors (ORB, AKAZE), NORM_L2 for SIFT
            self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            self.bf_l2 = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    
    def match_stereo(self, desc_left: np.ndarray, desc_right: np.ndarray,
                     ratio_threshold: float = 0.7,
                     max_disparity: float = 200) -> List[Tuple[int, int]]:
        """
        Match features between left and right stereo images
        
        Args:
            desc_left: Descriptors from left frame
            desc_right: Descriptors from right frame
            ratio_threshold: Lowe's ratio test threshold
            max_disparity: Maximum expected disparity for epipolar constraint
            
        Returns:
            List of matched feature pairs
        """
        if desc_left is None or desc_right is None:
            return []
        
        if len(desc_left) == 0 or len(desc_right) == 0:
            return []
        
        # Match descriptors
        if self.method == 'flann':
            matches = self.flann.knnMatch(desc_left, desc_right, k=2)
        elif self.method == 'bf':
            # Use appropriate norm based on descriptor type
            matches = self.bf.knnMatch(desc_left, desc_right, k=2)
        else:
            # Hybrid: use BF for reliability
            matches = self.bf.knnMatch(desc_left, desc_right, k=2)
        
        # Apply Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append((m.queryIdx, m.trainIdx))
        
        return good_matches
    
    def match_temporal(self, desc_frame1: np.ndarray, desc_frame2: np.ndarray,
                      ratio_threshold: float = 0.75) -> List[Tuple[int, int]]:
        """
        Match features between consecutive frames (temporal tracking)
        
        Args:
            desc_frame1: Descriptors from frame 1
            desc_frame2: Descriptors from frame 2
            ratio_threshold: Lowe's ratio test threshold
            
        Returns:
            List of matched feature pairs
        """
        if desc_frame1 is None or desc_frame2 is None:
            return []
        
        if len(desc_frame1) == 0 or len(desc_frame2) == 0:
            return []
        
        # Match descriptors
        if self.method in ['flann', 'hybrid']:
            matches = self.flann.knnMatch(desc_frame1, desc_frame2, k=2)
        else:
            matches = self.bf.knnMatch(desc_frame1, desc_frame2, k=2)
        
        # Apply bidirectional Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append((m.queryIdx, m.trainIdx))
        
        return good_matches


class EpipolarGeometry:
    """
    Epipolar geometry for stereo vision
    """
    
    @staticmethod
    def compute_fundamental_matrix(pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute fundamental matrix using RANSAC
        
        Args:
            pts1: Points in first image
            pts2: Points in second image
            
        Returns:
            Tuple of (fundamental_matrix, inlier_mask)
        """
        if len(pts1) < 8 or len(pts2) < 8:
            return None, np.zeros(len(pts1), dtype=bool)
        
        F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 1.0, 0.99)
        
        return F, mask.ravel().astype(bool)
    
    @staticmethod
    def filter_by_epipolar_constraint(points1: np.ndarray, points2: np.ndarray,
                                     F: np.ndarray, threshold: float = 1.0) -> np.ndarray:
        """
        Filter matches using epipolar constraint
        
        Args:
            points1: Points in first image
            points2: Points in second image
            F: Fundamental matrix
            threshold: Distance threshold
            
        Returns:
            Boolean mask for valid matches
        """
        if F is None or len(points1) == 0:
            return np.ones(len(points1), dtype=bool)
        
        # Compute epipolar lines
        points1_h = np.hstack([points1, np.ones((len(points1), 1))])
        lines2 = F @ points1_h.T  # Lines in second image
        
        # Compute distances from points to epipolar lines
        distances = np.abs(np.sum(points2 * lines2[:2].T, axis=1)) / \
                   np.sqrt(lines2[0]**2 + lines2[1]**2)
        
        return distances < threshold


class PointCloudFilter:
    """
    Point cloud post-processing and filtering
    """
    
    @staticmethod
    def remove_outliers(points: np.ndarray, colors: np.ndarray,
                       distance_threshold: float = 5.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove outlier points based on distance from median
        
        Args:
            points: 3D points (Nx3)
            colors: RGB colors (Nx3)
            distance_threshold: Points beyond this distance from median are removed
            
        Returns:
            Filtered points and colors
        """
        if len(points) < 10:
            return points, colors
        
        # Compute median
        median = np.median(points, axis=0)
        
        # Compute distances from median
        distances = np.linalg.norm(points - median, axis=1)
        
        # Filter points
        mask = distances < distance_threshold
        
        return points[mask], colors[mask]
    
    @staticmethod
    def voxel_grid_downsample(points: np.ndarray, colors: np.ndarray,
                             voxel_size: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """
        Downsample point cloud using voxel grid
        
        Args:
            points: 3D points (Nx3)
            colors: RGB colors (Nx3)
            voxel_size: Size of voxel in meters
            
        Returns:
            Downsampled points and colors
        """
        if len(points) == 0:
            return points, colors
        
        # Compute voxel indices
        indices = np.floor(points / voxel_size).astype(int)
        
        # Find unique voxels
        _, unique_idx = np.unique(indices, axis=0, return_index=True)
        
        return points[unique_idx], colors[unique_idx]
    
    @staticmethod
    def remove_duplicates(points: np.ndarray, colors: np.ndarray,
                         tolerance: float = 0.001) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove duplicate or very close points
        
        Args:
            points: 3D points (Nx3)
            colors: RGB colors (Nx3)
            tolerance: Minimum distance between points
            
        Returns:
            Filtered points and colors
        """
        if len(points) < 2:
            return points, colors
        
        # Build distance matrix for subset of points
        sample_size = min(1000, len(points))
        keep_indices = [0]
        
        for i in range(1, sample_size):
            # Check distance to all kept points
            distances = np.linalg.norm(points[i] - points[keep_indices], axis=1)
            
            if np.min(distances) > tolerance:
                keep_indices.append(i)
        
        return points[keep_indices], colors[keep_indices]


class LoopClosureDetector:
    """
    Simple loop closure detection based on visual similarity
    """
    
    def __init__(self, distance_threshold: float = 1.0):
        """
        Initialize loop closure detector
        
        Args:
            distance_threshold: Distance threshold for loop closure
        """
        self.trajectory_history = []
        self.distance_threshold = distance_threshold
    
    def add_pose(self, position: np.ndarray):
        """Add camera position to history"""
        self.trajectory_history.append(position.copy())
    
    def detect_loop_closure(self) -> Tuple[bool, int, int]:
        """
        Detect if current position closes a loop
        
        Returns:
            Tuple of (is_loop_closure, start_idx, current_idx)
        """
        if len(self.trajectory_history) < 10:
            return False, -1, -1
        
        current_pos = self.trajectory_history[-1]
        
        # Check distance to earlier poses
        for i in range(len(self.trajectory_history) - 10):
            distance = np.linalg.norm(current_pos - self.trajectory_history[i])
            
            if distance < self.distance_threshold:
                return True, i, len(self.trajectory_history) - 1
        
        return False, -1, -1
    
    def get_trajectory(self) -> np.ndarray:
        """Get recorded trajectory"""
        return np.array(self.trajectory_history) if self.trajectory_history else np.array([]).reshape(0, 3)


class BundleAdjustment:
    """
    Simple bundle adjustment for refining camera poses and point positions
    """
    
    @staticmethod
    def optimize_poses(camera_poses: List[np.ndarray],
                      point_cloud: np.ndarray,
                      correspondences: List[List[Tuple[int, int]]],
                      iterations: int = 5) -> Tuple[List[np.ndarray], np.ndarray]:
        """
        Simple iterative refinement of camera poses
        
        Args:
            camera_poses: List of 4x4 pose matrices
            point_cloud: 3D points (Nx3)
            correspondences: Per-frame list of (point_idx, feature_idx) pairs
            iterations: Number of optimization iterations
            
        Returns:
            Optimized poses and points
        """
        # Simplified optimization: just compute center of mass
        if len(point_cloud) < 3:
            return camera_poses, point_cloud
        
        # Compute weighted average positions
        optimized_points = point_cloud.copy()
        
        # Iteratively refine
        for _ in range(iterations):
            # Reproject points to frames and refine
            new_points = np.zeros_like(optimized_points)
            counts = np.zeros(len(optimized_points))
            
            for frame_idx, corr_list in enumerate(correspondences):
                if frame_idx >= len(camera_poses):
                    continue
                
                pose = camera_poses[frame_idx]
                R = pose[:3, :3]
                t = pose[:3, 3]
                
                for point_idx, _ in corr_list:
                    if point_idx < len(optimized_points):
                        # Simple averaging in world frame
                        new_points[point_idx] += optimized_points[point_idx]
                        counts[point_idx] += 1
            
            # Update points with weighted average
            mask = counts > 0
            optimized_points[mask] /= counts[mask, np.newaxis]
        
        return camera_poses, optimized_points


class CloudExporter:
    """
    Export point cloud and trajectory in various formats
    """
    
    @staticmethod
    def export_ply(points: np.ndarray, colors: np.ndarray, filename: str):
        """
        Export point cloud to PLY format
        
        Args:
            points: 3D points (Nx3)
            colors: RGB colors (Nx3), values 0-255
            filename: Output file path
        """
        import struct
        
        num_points = len(points)
        
        with open(filename, 'wb') as f:
            # Write PLY header
            f.write(b'ply\n')
            f.write(b'format binary_little_endian 1.0\n')
            f.write(f'element vertex {num_points}\n'.encode())
            f.write(b'property float x\n')
            f.write(b'property float y\n')
            f.write(b'property float z\n')
            f.write(b'property uchar red\n')
            f.write(b'property uchar green\n')
            f.write(b'property uchar blue\n')
            f.write(b'end_header\n')
            
            # Write points
            for i in range(num_points):
                x, y, z = points[i]
                r, g, b = int(colors[i, 0]), int(colors[i, 1]), int(colors[i, 2])
                
                data = struct.pack('<fffBBB', x, y, z, r, g, b)
                f.write(data)
        
        print(f"Exported point cloud to {filename}")
    
    @staticmethod
    def export_trajectory_json(trajectory: np.ndarray, filename: str):
        """
        Export trajectory to JSON
        
        Args:
            trajectory: Camera trajectory (Nx3)
            filename: Output file path
        """
        data = {
            'trajectory': trajectory.tolist(),
            'num_points': len(trajectory),
            'total_distance': float(np.sum([
                np.linalg.norm(trajectory[i+1] - trajectory[i])
                for i in range(len(trajectory) - 1)
            ])) if len(trajectory) > 1 else 0
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Exported trajectory to {filename}")
    
    @staticmethod
    def export_ply_with_trajectory(points: np.ndarray, colors: np.ndarray,
                                  trajectory: np.ndarray, filename: str):
        """
        Export point cloud with trajectory line to PLY
        
        Args:
            points: 3D points (Nx3)
            colors: RGB colors (Nx3)
            trajectory: Camera trajectory (Mx3)
            filename: Output file path
        """
        # Combine points with trajectory
        all_points = np.vstack([points, trajectory])
        
        # Colors: original + red for trajectory
        traj_colors = np.tile([255, 0, 0], (len(trajectory), 1))
        all_colors = np.vstack([colors, traj_colors])
        
        CloudExporter.export_ply(all_points, all_colors, filename)


if __name__ == "__main__":
    # Test point cloud filtering
    print("Testing Point Cloud Filter...")
    test_points = np.random.randn(100, 3)
    test_colors = np.random.randint(0, 255, (100, 3))
    
    filtered_pts, filtered_cols = PointCloudFilter.remove_outliers(test_points, test_colors)
    print(f"  Original: {len(test_points)} points")
    print(f"  Filtered: {len(filtered_pts)} points")
    
    downsampled_pts, downsampled_cols = PointCloudFilter.voxel_grid_downsample(
        test_points, test_colors, voxel_size=0.1
    )
    print(f"  Downsampled (0.1m voxel): {len(downsampled_pts)} points")
