"""
SLAM Real-time Viewer
Interactive visualization of stereo camera feeds, 2D map overlay, 3D map, and system statistics
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import numpy as np
import cv2
from PIL import Image, ImageTk
import threading
import json
from collections import deque
from typing import Dict, Optional, Callable


class SLAMViewer(ctk.CTkToplevel):
    """
    Interactive SLAM visualization window with:
    - Left/Right stereo camera feeds with 2D map overlay
    - 3D map visualization
    - Battery level and system statistics
    - Edit config button
    """
    
    def __init__(self, parent, on_config_edit: Optional[Callable] = None):
        """
        Initialize SLAM viewer
        
        Args:
            parent: Parent widget
            on_config_edit: Callback when edit config is clicked
        """
        super().__init__(parent)
        self.title("SLAM Real-time Viewer")
        self.geometry("1600x900")
        self.minsize(1400, 800)
        
        self.on_config_edit = on_config_edit
        
        # Data storage
        self.current_left_frame = None
        self.current_right_frame = None
        self.map_2d = None
        self.map_3d = None
        self.battery_level = 100.0
        self.camera_pose = np.eye(4)
        self.point_cloud = np.array([]).reshape(0, 3)
        self.trajectory = deque(maxlen=1000)
        
        # Statistics
        self.stats = {
            'fps': 0,
            'features_detected': 0,
            'landmarks': 0,
            'keyframes': 0,
            'trajectory_length': 0.0,
            'loop_closures': 0,
            'degradation_level': 'L0'
        }
        
        self.is_running = True
        self.lock = threading.Lock()
        
        self._create_layout()
        
    def _create_layout(self):
        """Create main layout"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header with title and edit config button
        self._create_header(main_frame)
        
        # Content area
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Top section: Stereo camera feeds
        self._create_camera_section(content_frame)
        
        # Bottom section: Maps and statistics
        self._create_maps_and_stats_section(content_frame)
        
    def _create_header(self, parent):
        """Create header with title and edit config button"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="SLAM Real-time Visualization",
            font=("Segoe UI", 18, "bold"),
            text_color="#00FF00"
        )
        title_label.pack(side="left")
        
        # Spacer
        spacer = ctk.CTkFrame(header_frame, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
        # Edit config button
        edit_btn = ctk.CTkButton(
            header_frame,
            text="⚙ Edit Config",
            font=("Segoe UI", 12, "bold"),
            width=140,
            height=35,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._on_edit_config
        )
        edit_btn.pack(side="right", padx=5)
        
    def _on_edit_config(self):
        """Handle edit config button click"""
        if self.on_config_edit:
            self.on_config_edit()
        else:
            messagebox.showinfo("Edit Config", "Configuration editor not connected")
    
    def _create_camera_section(self, parent):
        """Create stereo camera feed section"""
        camera_frame = ctk.CTkFrame(parent)
        camera_frame.pack(fill="both", expand=False, pady=(0, 10))
        
        # Left camera
        left_cam_frame = ctk.CTkFrame(camera_frame, fg_color="#1a1a1a", border_width=2, border_color="#00FF00")
        left_cam_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Label
        left_label = ctk.CTkLabel(
            left_cam_frame,
            text="Left Camera Feed",
            font=("Segoe UI", 11, "bold"),
            text_color="#00FF00"
        )
        left_label.pack(pady=5)
        
        # Camera canvas
        self.left_cam_canvas = ctk.CTkCanvas(
            left_cam_frame,
            width=640,
            height=360,
            bg="#000000",
            highlightthickness=0
        )
        self.left_cam_canvas.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Right camera
        right_cam_frame = ctk.CTkFrame(camera_frame, fg_color="#1a1a1a", border_width=2, border_color="#00FF00")
        right_cam_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Label
        right_label = ctk.CTkLabel(
            right_cam_frame,
            text="Right Camera Feed",
            font=("Segoe UI", 11, "bold"),
            text_color="#00FF00"
        )
        right_label.pack(pady=5)
        
        # Camera canvas
        self.right_cam_canvas = ctk.CTkCanvas(
            right_cam_frame,
            width=640,
            height=360,
            bg="#000000",
            highlightthickness=0
        )
        self.right_cam_canvas.pack(fill="both", expand=True, padx=5, pady=(0, 5))
    
    def _create_maps_and_stats_section(self, parent):
        """Create maps and statistics section"""
        bottom_frame = ctk.CTkFrame(parent)
        bottom_frame.pack(fill="both", expand=True)
        
        # Left: 2D Map
        map_2d_frame = ctk.CTkFrame(bottom_frame, fg_color="#1a1a1a", border_width=2, border_color="#0099FF")
        map_2d_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        map_2d_label = ctk.CTkLabel(
            map_2d_frame,
            text="2D Map",
            font=("Segoe UI", 12, "bold"),
            text_color="#0099FF"
        )
        map_2d_label.pack(pady=5)
        
        self.map_2d_canvas = ctk.CTkCanvas(
            map_2d_frame,
            width=400,
            height=400,
            bg="#000000",
            highlightthickness=0
        )
        self.map_2d_canvas.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Middle: 3D Map
        map_3d_frame = ctk.CTkFrame(bottom_frame, fg_color="#1a1a1a", border_width=2, border_color="#FF9900")
        map_3d_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        map_3d_label = ctk.CTkLabel(
            map_3d_frame,
            text="3D Map",
            font=("Segoe UI", 12, "bold"),
            text_color="#FF9900"
        )
        map_3d_label.pack(pady=5)
        
        self.map_3d_canvas = ctk.CTkCanvas(
            map_3d_frame,
            width=400,
            height=400,
            bg="#000000",
            highlightthickness=0
        )
        self.map_3d_canvas.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Right: Battery & Statistics
        stats_frame = ctk.CTkFrame(bottom_frame, fg_color="#1a1a1a", border_width=2, border_color="#FF6B6B")
        stats_frame.pack(side="right", fill="both", expand=False, padx=(5, 0), ipadx=10, ipady=10)
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text="System Statistics",
            font=("Segoe UI", 12, "bold"),
            text_color="#FF6B6B"
        )
        stats_label.pack(pady=10)
        
        # Battery level
        battery_label = ctk.CTkLabel(
            stats_frame,
            text="Battery Level",
            font=("Segoe UI", 10, "bold"),
            text_color="#FFFFFF"
        )
        battery_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        self.battery_label = ctk.CTkLabel(
            stats_frame,
            text="100.0%",
            font=("Segoe UI", 14, "bold"),
            text_color="#00FF00"
        )
        self.battery_label.pack(anchor="w", padx=10)
        
        # Battery progress bar
        self.battery_progress = ctk.CTkProgressBar(stats_frame, width=150)
        self.battery_progress.pack(padx=10, pady=(0, 10), fill="x")
        self.battery_progress.set(1.0)
        
        # Degradation level
        self.degradation_label = ctk.CTkLabel(
            stats_frame,
            text="Degradation: L0",
            font=("Segoe UI", 10),
            text_color="#00FF00"
        )
        self.degradation_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Separator
        sep1 = ctk.CTkFrame(stats_frame, height=1, fg_color="#444444")
        sep1.pack(fill="x", padx=10, pady=10)
        
        # Statistics grid
        stats_data = [
            ("FPS", "fps"),
            ("Features", "features_detected"),
            ("Landmarks", "landmarks"),
            ("Keyframes", "keyframes"),
            ("Trajectory (m)", "trajectory_length"),
            ("Loop Closures", "loop_closures"),
        ]
        
        self.stat_labels = {}
        for label_text, stat_key in stats_data:
            label = ctk.CTkLabel(
                stats_frame,
                text=f"{label_text}:",
                font=("Segoe UI", 9),
                text_color="#AAAAAA"
            )
            label.pack(anchor="w", padx=10, pady=2)
            
            value_label = ctk.CTkLabel(
                stats_frame,
                text="0",
                font=("Segoe UI", 10, "bold"),
                text_color="#00FF00"
            )
            value_label.pack(anchor="w", padx=20, pady=2)
            self.stat_labels[stat_key] = value_label
    
    def update_camera_feeds(self, left_frame: np.ndarray, right_frame: np.ndarray):
        """
        Update camera feeds with new frames
        
        Args:
            left_frame: Left camera frame (BGR)
            right_frame: Right camera frame (BGR)
        """
        with self.lock:
            self.current_left_frame = left_frame.copy() if left_frame is not None else None
            self.current_right_frame = right_frame.copy() if right_frame is not None else None
        
        # Schedule canvas update
        self.after(0, self._update_camera_display)
    
    def _update_camera_display(self):
        """Update camera display on canvas"""
        with self.lock:
            left_frame = self.current_left_frame
            right_frame = self.current_right_frame
        
        if left_frame is not None:
            # Resize to canvas size
            left_resized = cv2.resize(left_frame, (640, 360))
            left_rgb = cv2.cvtColor(left_resized, cv2.COLOR_BGR2RGB)
            left_img = Image.fromarray(left_rgb)
            left_photo = ImageTk.PhotoImage(left_img)
            
            self.left_cam_canvas.create_image(0, 0, anchor="nw", image=left_photo)
            self.left_cam_canvas.image = left_photo
        
        if right_frame is not None:
            # Resize to canvas size
            right_resized = cv2.resize(right_frame, (640, 360))
            right_rgb = cv2.cvtColor(right_resized, cv2.COLOR_BGR2RGB)
            right_img = Image.fromarray(right_rgb)
            right_photo = ImageTk.PhotoImage(right_img)
            
            self.right_cam_canvas.create_image(0, 0, anchor="nw", image=right_photo)
            self.right_cam_canvas.image = right_photo
    
    def update_2d_map(self, map_image: np.ndarray):
        """
        Update 2D map display
        
        Args:
            map_image: 2D map as numpy array
        """
        with self.lock:
            self.map_2d = map_image.copy() if map_image is not None else None
        
        self.after(0, self._update_2d_map_display)
    
    def _update_2d_map_display(self):
        """Update 2D map on canvas"""
        with self.lock:
            map_2d = self.map_2d
        
        if map_2d is not None:
            # Resize to canvas size
            map_resized = cv2.resize(map_2d, (400, 400))
            
            # Convert to RGB if grayscale
            if len(map_resized.shape) == 2:
                map_resized = cv2.cvtColor(map_resized, cv2.COLOR_GRAY2RGB)
            else:
                map_resized = cv2.cvtColor(map_resized, cv2.COLOR_BGR2RGB)
            
            map_img = Image.fromarray(map_resized)
            map_photo = ImageTk.PhotoImage(map_img)
            
            self.map_2d_canvas.create_image(0, 0, anchor="nw", image=map_photo)
            self.map_2d_canvas.image = map_photo
    
    def update_3d_map(self, point_cloud: np.ndarray, trajectory: deque = None):
        """
        Update 3D map visualization
        
        Args:
            point_cloud: 3D points array (Nx3)
            trajectory: Camera trajectory points
        """
        with self.lock:
            self.point_cloud = point_cloud.copy() if point_cloud is not None else np.array([]).reshape(0, 3)
            if trajectory is not None:
                self.trajectory = deque(trajectory, maxlen=1000)
        
        self.after(0, self._update_3d_map_display)
    
    def _update_3d_map_display(self):
        """Update 3D map visualization"""
        self.map_3d_canvas.delete("all")
        
        with self.lock:
            point_cloud = self.point_cloud
            trajectory = list(self.trajectory)
        
        if point_cloud is None or point_cloud.shape[0] == 0:
            self._draw_placeholder(self.map_3d_canvas, "3D Map")
            return
        
        # Project 3D points to 2D canvas (top-down view)
        canvas_width = 400
        canvas_height = 400
        
        # Get bounds
        if point_cloud.shape[0] > 0:
            x_min, y_min = point_cloud[:, 0].min(), point_cloud[:, 1].min()
            x_max, y_max = point_cloud[:, 0].max(), point_cloud[:, 1].max()
            
            # Add padding
            x_range = x_max - x_min if x_max > x_min else 1
            y_range = y_max - y_min if y_max > y_min else 1
            padding = max(x_range, y_range) * 0.1
            
            x_min -= padding
            x_max += padding
            y_min -= padding
            y_max += padding
            
            # Draw point cloud
            for point in point_cloud[::max(1, len(point_cloud)//500)]:  # Sample points
                # Project to canvas
                x_norm = (point[0] - x_min) / (x_max - x_min) if x_max > x_min else 0.5
                y_norm = (point[1] - y_min) / (y_max - y_min) if y_max > y_min else 0.5
                
                canvas_x = int(x_norm * canvas_width)
                canvas_y = int(y_norm * canvas_height)
                
                # Clamp to canvas
                canvas_x = max(0, min(canvas_width - 1, canvas_x))
                canvas_y = max(0, min(canvas_height - 1, canvas_y))
                
                self.map_3d_canvas.create_oval(
                    canvas_x - 1, canvas_y - 1,
                    canvas_x + 1, canvas_y + 1,
                    fill="#0099FF", outline="#0099FF"
                )
            
            # Draw trajectory
            if trajectory and len(trajectory) > 1:
                trajectory_points = []
                for pose in trajectory:
                    if isinstance(pose, np.ndarray) and pose.shape == (4, 4):
                        x, y = pose[0, 3], pose[1, 3]
                    else:
                        continue
                    
                    x_norm = (x - x_min) / (x_max - x_min) if x_max > x_min else 0.5
                    y_norm = (y - y_min) / (y_max - y_min) if y_max > y_min else 0.5
                    
                    canvas_x = int(x_norm * canvas_width)
                    canvas_y = int(y_norm * canvas_height)
                    
                    trajectory_points.append((canvas_x, canvas_y))
                
                # Draw trajectory line
                for i in range(len(trajectory_points) - 1):
                    x1, y1 = trajectory_points[i]
                    x2, y2 = trajectory_points[i + 1]
                    self.map_3d_canvas.create_line(
                        x1, y1, x2, y2,
                        fill="#FF6B6B", width=2
                    )
    
    def _draw_placeholder(self, canvas: ctk.CTkCanvas, text: str):
        """Draw placeholder text on canvas"""
        canvas.delete("all")
        canvas.create_text(
            canvas.winfo_width() // 2,
            canvas.winfo_height() // 2,
            text=text,
            fill="#666666",
            font=("Segoe UI", 12)
        )
    
    def update_statistics(self, stats: Dict):
        """
        Update statistics display
        
        Args:
            stats: Dictionary with statistics keys
        """
        with self.lock:
            self.stats.update(stats)
        
        self.after(0, self._update_stats_display)
    
    def update_battery(self, level: float, degradation_level: str = "L0"):
        """
        Update battery display
        
        Args:
            level: Battery level 0-100
            degradation_level: Degradation level string
        """
        with self.lock:
            self.battery_level = max(0, min(100, level))
            self.stats['degradation_level'] = degradation_level
        
        self.after(0, self._update_battery_display)
    
    def _update_battery_display(self):
        """Update battery display on UI"""
        with self.lock:
            level = self.battery_level
            degradation = self.stats['degradation_level']
        
        # Update battery label and progress
        self.battery_label.configure(text=f"{level:.1f}%")
        self.battery_progress.set(level / 100.0)
        
        # Color based on level
        if level >= 60:
            color = "#00FF00"
        elif level >= 30:
            color = "#FFFF00"
        else:
            color = "#FF6B6B"
        
        self.battery_label.configure(text_color=color)
        
        # Update degradation level
        if degradation == "L0":
            deg_color = "#00FF00"
        elif degradation == "L1":
            deg_color = "#FFFF00"
        elif degradation == "L2":
            deg_color = "#FF9900"
        else:
            deg_color = "#FF6B6B"
        
        self.degradation_label.configure(
            text=f"Degradation: {degradation}",
            text_color=deg_color
        )
    
    def _update_stats_display(self):
        """Update statistics display"""
        with self.lock:
            stats = self.stats.copy()
        
        # Update each statistic label
        for stat_key, label_widget in self.stat_labels.items():
            if stat_key in stats:
                value = stats[stat_key]
                if isinstance(value, float):
                    text = f"{value:.2f}"
                else:
                    text = str(value)
                label_widget.configure(text=text)
    
    def on_closing(self):
        """Handle window closing"""
        self.is_running = False
        self.destroy()
