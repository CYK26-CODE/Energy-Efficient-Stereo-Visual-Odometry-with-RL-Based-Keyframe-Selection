#!/usr/bin/env python3
"""
Professional DQN SLAM Training Dashboard - Complete Integration
Full-featured UI for training, monitoring, and configuring DQN agents
"""

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import cv2
from typing import Dict, Callable, Optional
import threading
import json
from datetime import datetime
from pathlib import Path

# Import custom modules
from backend_interface import BackendInterface, ConfigurationManager
from reward_configurator import RewardConfigurator
from degradation_configurator import BatteryDegradationConfigurator
from metrics_visualizer import RealtimeMetricsDisplay
from real_slam_viewer import RealSLAMViewer
from adaptive_camera import AdaptiveCameraManager

# Import SLAM backend
import sys
from pathlib import Path
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'runtime'))
    from stereo_slam import StereoSLAMSystem
    from integrated_slam import IntegratedStereoSLAMSystem
    from synthetic_stereo import SyntheticStereoGenerator, MockCameraStream
except ImportError as e:
    print(f"Warning: Could not import SLAM modules: {e}")
    StereoSLAMSystem = None
    IntegratedStereoSLAMSystem = None
    SyntheticStereoGenerator = None
    MockCameraStream = None


class AdvancedDQNTrainingDashboard(ctk.CTk):
    """Advanced training dashboard with full integration"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("🤖 DQN SLAM Training System - Professional Dashboard")
        self.geometry("1800x1000")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        # Initialize backend interface
        self.backend = BackendInterface()
        self.config_manager = ConfigurationManager()
        
        # Initialize integrated SLAM system (connects to ESP32 cameras or synthetic)
        self.slam_system = None
        self.slam_thread = None
        self.slam_running = False
        self.slam_config = {
            'left_camera_url': 'http://192.168.1.100/stream',
            'right_camera_url': 'http://192.168.1.101/stream'
        }
        
        # Register backend callbacks
        self.backend.on_episode_complete = self._on_episode_complete
        self.backend.on_training_start = self._on_training_start
        self.backend.on_training_stop = self._on_training_stop
        
        # Metrics display
        self.metrics_window = None
        
        # SLAM Viewer
        self.slam_viewer = None
        
        # Build UI
        self._create_layout()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_layout(self):
        """Create main layout"""
        
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create header
        self._create_header(main_frame)
        
        # Content area with 3 main sections
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left panel: Training controls
        left_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_panel.pack(side="left", fill="y", expand=False, padx=(0, 10))
        
        self._create_training_control_section(left_panel)
        
        # Middle panel: Configuration
        middle_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        middle_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self._create_configuration_section(middle_panel)
        
        # Right panel: Statistics
        right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_panel.pack(side="right", fill="y", expand=False, padx=(0, 0))
        
        self._create_statistics_section(right_panel)
    
    def _create_header(self, parent):
        """Create header with title and status"""
        header = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=12, height=70)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(
            title_frame, text="🚀 DQN SLAM INTELLIGENT TRAINING SYSTEM",
            font=("Roboto", 18, "bold"), text_color="#00ff00"
        ).pack(side="left", anchor="w")
        
        ctk.CTkLabel(
            title_frame, text="Real-time Learning with Battery-Aware Keyframe Selection",
            font=("Roboto", 10), text_color="#808080"
        ).pack(side="left", anchor="w", padx=20)
        
        # Status indicator
        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side="right", padx=20, pady=15)
        
        # Status indicator dot
        self.status_indicator = ctk.CTkLabel(
            status_frame, text="●", font=("Roboto", 20), text_color="#ff4444"
        )
        self.status_indicator.pack(side="left", padx=(0, 10))
        
        # Status text
        self.status_text = ctk.CTkLabel(
            status_frame, text="IDLE", font=("Roboto", 12, "bold"), text_color="#ff4444"
        )
        self.status_text.pack(side="left")
    
    def _create_training_control_section(self, parent):
        """Create training control panel"""
        
        # Frame
        frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=12)
        frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Title
        ctk.CTkLabel(
            frame, text="🎮 TRAINING CONTROL",
            font=("Roboto", 13, "bold"), text_color="#00ff00"
        ).pack(pady=12, padx=15, anchor="w")
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Episode configuration
        ctk.CTkLabel(scroll_frame, text="Episodes", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.episodes_entry = ctk.CTkEntry(scroll_frame, placeholder_text="500")
        self.episodes_entry.pack(fill="x", pady=(0, 10))
        self.episodes_entry.insert(0, "500")
        
        # Battery profile
        ctk.CTkLabel(scroll_frame, text="Battery Profile", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.battery_var = ctk.StringVar(value="declining")
        ctk.CTkOptionMenu(
            scroll_frame, values=["constant", "declining", "variable"],
            variable=self.battery_var, width=200
        ).pack(fill="x", pady=(0, 10))
        
        # Device selection
        ctk.CTkLabel(scroll_frame, text="Device", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.device_var = ctk.StringVar(value="CPU")
        device_menu = ctk.CTkOptionMenu(
            scroll_frame, values=["CPU", "CUDA (GPU)"],
            variable=self.device_var, width=200
        )
        device_menu.pack(fill="x", pady=(0, 20))
        
        # Progress bar
        ctk.CTkLabel(scroll_frame, text="Progress", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(5, 5))
        self.progress_bar = ctk.CTkProgressBar(scroll_frame, height=8)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)
        
        # Progress text
        self.progress_text = ctk.CTkLabel(
            scroll_frame, text="0 / 500 episodes", font=("Roboto", 9), text_color="#808080"
        )
        self.progress_text.pack(anchor="e", pady=(0, 20))
        
        # Divider
        ctk.CTkFrame(scroll_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Training buttons
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))
        
        self.start_btn = ctk.CTkButton(
            button_frame, text="▶ START", command=self._start_training,
            fg_color="#2E7D32", hover_color="#1b5620", height=45,
            font=("Roboto", 12, "bold")
        )
        self.start_btn.pack(fill="x", pady=(0, 5))
        
        button_row = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_row.pack(fill="x", pady=5)
        
        self.pause_btn = ctk.CTkButton(
            button_row, text="⏸ PAUSE", command=self._pause_training,
            fg_color="#ff9800", hover_color="#e68900", height=40,
            font=("Roboto", 11, "bold")
        )
        self.pause_btn.pack(side="left", fill="both", expand=True, padx=(0, 3))
        
        self.stop_btn = ctk.CTkButton(
            button_row, text="⏹ STOP", command=self._stop_training,
            fg_color="#d32f2f", hover_color="#b71c1c", height=40,
            font=("Roboto", 11, "bold")
        )
        self.stop_btn.pack(side="right", fill="both", expand=True, padx=(3, 0))
        
        # Divider
        ctk.CTkFrame(scroll_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Model management
        ctk.CTkLabel(scroll_frame, text="Model Management", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        model_buttons = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        model_buttons.pack(fill="x")
        
        self.save_btn = ctk.CTkButton(
            model_buttons, text="💾 SAVE", command=self._save_model,
            fg_color="#0066cc", hover_color="#004499", height=40,
            font=("Roboto", 10, "bold")
        )
        self.save_btn.pack(side="left", fill="both", expand=True, padx=(0, 3))
        
        self.load_btn = ctk.CTkButton(
            model_buttons, text="📂 LOAD", command=self._load_model,
            fg_color="#0066cc", hover_color="#004499", height=40,
            font=("Roboto", 10, "bold")
        )
        self.load_btn.pack(side="right", fill="both", expand=True, padx=(3, 0))
        
        # Divider
        ctk.CTkFrame(scroll_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Export metrics
        ctk.CTkLabel(scroll_frame, text="Export Results", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        export_btn = ctk.CTkButton(
            scroll_frame, text="📊 EXPORT METRICS", command=self._export_metrics,
            fg_color="#00aa66", hover_color="#007744", height=40,
            font=("Roboto", 10, "bold")
        )
        export_btn.pack(fill="x")
        
        # Divider
        ctk.CTkFrame(scroll_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # SLAM Viewer
        ctk.CTkLabel(scroll_frame, text="SLAM Visualization", font=("Roboto", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        slam_btn = ctk.CTkButton(
            scroll_frame, text="🎬 SLAM VIEWER", command=self._open_slam_viewer,
            fg_color="#9c27b0", hover_color="#6a1b9a", height=40,
            font=("Roboto", 10, "bold")
        )
        slam_btn.pack(fill="x")
    
    def _create_configuration_section(self, parent):
        """Create configuration section"""
        
        frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=12)
        frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Title
        ctk.CTkLabel(
            frame, text="⚙️ SYSTEM CONFIGURATION",
            font=("Roboto", 13, "bold"), text_color="#00ff00"
        ).pack(pady=12, padx=15, anchor="w")
        
        # Tabs (using frames)
        tab_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tab_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.config_tabs = {}
        
        # DQN Parameters button
        dqn_btn = ctk.CTkButton(
            tab_frame, text="🧠 DQN PARAMS", width=100, height=35,
            command=self._show_dqn_config,
            fg_color="#0066cc", hover_color="#004499",
            font=("Roboto", 10, "bold")
        )
        dqn_btn.pack(side="left", padx=3)
        self.config_tabs['dqn'] = dqn_btn
        
        # Reward Weights button
        reward_btn = ctk.CTkButton(
            tab_frame, text="⚖️ REWARDS", width=100, height=35,
            command=self._show_reward_config,
            fg_color="#0066cc", hover_color="#004499",
            font=("Roboto", 10, "bold")
        )
        reward_btn.pack(side="left", padx=3)
        self.config_tabs['reward'] = reward_btn
        
        # Battery Degradation button
        battery_btn = ctk.CTkButton(
            tab_frame, text="🔋 BATTERY", width=100, height=35,
            command=self._show_degradation_config,
            fg_color="#0066cc", hover_color="#004499",
            font=("Roboto", 10, "bold")
        )
        battery_btn.pack(side="left", padx=3)
        self.config_tabs['battery'] = battery_btn
        
        # Metrics Display button
        metrics_btn = ctk.CTkButton(
            tab_frame, text="📈 METRICS", width=100, height=35,
            command=self._show_metrics,
            fg_color="#0066cc", hover_color="#004499",
            font=("Roboto", 10, "bold")
        )
        metrics_btn.pack(side="left", padx=3)
        self.config_tabs['metrics'] = metrics_btn
        
        # Content area
        self.config_content = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.config_content.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Default: show DQN parameters
        self._show_dqn_config()
    
    def _show_dqn_config(self):
        """Show DQN parameters configuration"""
        self._clear_config_content()
        
        # Update button color
        for name, btn in self.config_tabs.items():
            color = "#ff9800" if name == 'dqn' else "#0066cc"
            btn.configure(fg_color=color)
        
        # Create parameter sliders
        ctk.CTkLabel(
            self.config_content, text="DQN Hyperparameters",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 10))
        
        # Learning Rate
        self._create_param_slider(
            self.config_content, "Learning Rate (lr)", 1e-5, 1e-3,
            self.backend.config["learning_rate"], decimals=5
        )
        
        # Gamma
        self._create_param_slider(
            self.config_content, "Discount Factor (γ)", 0.9, 0.99,
            self.backend.config["gamma"], decimals=3
        )
        
        # Epsilon Start
        self._create_param_slider(
            self.config_content, "Exploration Start (ε_start)", 0.1, 1.0,
            self.backend.config["epsilon_start"], decimals=2
        )
        
        # Epsilon End
        self._create_param_slider(
            self.config_content, "Exploration End (ε_end)", 0.01, 0.2,
            self.backend.config["epsilon_end"], decimals=3
        )
        
        # Batch Size
        self._create_param_slider(
            self.config_content, "Batch Size", 16, 256,
            self.backend.config["batch_size"], decimals=0
        )
        
        # Update Frequency
        self._create_param_slider(
            self.config_content, "Target Update Frequency", 100, 5000,
            1000, decimals=0
        )
    
    def _show_reward_config(self):
        """Show reward configuration"""
        self._clear_config_content()
        
        # Update button color
        for name, btn in self.config_tabs.items():
            color = "#ff9800" if name == 'reward' else "#0066cc"
            btn.configure(fg_color=color)
        
        def on_reward_save(weights):
            self.backend.update_reward_weights(weights)
        
        # Create inline reward configuration
        ctk.CTkLabel(
            self.config_content, text="Reward Weight Configuration",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 10))
        
        # Quick preset buttons
        preset_frame = ctk.CTkFrame(self.config_content, fg_color="transparent")
        preset_frame.pack(fill="x", pady=10)
        
        presets = {
            "Conservative": {"w_b": 12.0, "w_e": 10.0, "w_l": 50.0, "w_t": 0.02},
            "Balanced": {"w_b": 8.0, "w_e": 6.0, "w_l": 40.0, "w_t": 0.01},
            "Aggressive": {"w_b": 4.0, "w_e": 2.0, "w_l": 30.0, "w_t": 0.005}
        }
        
        for name, values in presets.items():
            ctk.CTkButton(
                preset_frame, text=name, width=80, height=30,
                command=lambda v=values: self.backend.update_reward_weights(v),
                fg_color="#0066cc", hover_color="#004499",
                font=("Roboto", 9, "bold")
            ).pack(side="left", padx=3, fill="x", expand=True)
        
        # Open configurator button
        ctk.CTkButton(
            self.config_content, text="🎛️ ADVANCED CONFIGURATOR",
            command=self._open_reward_configurator, height=45,
            fg_color="#ff6600", hover_color="#cc5200",
            font=("Roboto", 11, "bold")
        ).pack(fill="x", pady=(10, 20))
        
        # Display current weights
        weights = self.backend.config.get("reward_weights", {})
        ctk.CTkLabel(
            self.config_content, text="Current Weights:",
            font=("Roboto", 10, "bold"), text_color="#00ff00"
        ).pack(anchor="w", pady=(10, 5))
        
        for key, value in weights.items():
            row = ctk.CTkFrame(self.config_content, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{key}:", font=("Roboto", 9)).pack(side="left")
            ctk.CTkLabel(row, text=f"{value:.3f}", font=("Roboto", 9, "bold"), text_color="#00ff00").pack(side="right")
    
    def _show_degradation_config(self):
        """Show battery degradation configuration"""
        self._clear_config_content()
        
        # Update button color
        for name, btn in self.config_tabs.items():
            color = "#ff9800" if name == 'battery' else "#0066cc"
            btn.configure(fg_color=color)
        
        ctk.CTkLabel(
            self.config_content, text="Battery Degradation Levels",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 10))
        
        # Preset buttons
        preset_frame = ctk.CTkFrame(self.config_content, fg_color="transparent")
        preset_frame.pack(fill="x", pady=10)
        
        presets = {
            "Conservative": [70, 50, 25],
            "Balanced": [60, 40, 20],
            "Aggressive": [50, 30, 15]
        }
        
        for name, thresholds in presets.items():
            ctk.CTkButton(
                preset_frame, text=name, width=80, height=30,
                command=lambda t=thresholds: self.backend.update_battery_thresholds(t),
                fg_color="#0066cc", hover_color="#004499",
                font=("Roboto", 9, "bold")
            ).pack(side="left", padx=3, fill="x", expand=True)
        
        # Open configurator
        ctk.CTkButton(
            self.config_content, text="🔧 ADVANCED CONFIGURATOR",
            command=self._open_degradation_configurator, height=45,
            fg_color="#ff6600", hover_color="#cc5200",
            font=("Roboto", 11, "bold")
        ).pack(fill="x", pady=(10, 20))
        
        # Display current thresholds
        thresholds = self.backend.config.get("battery_thresholds", [60, 40, 20])
        
        levels_info = [
            ("Level 0", f"≥ {thresholds[0]}%", "#2E7D32", "Full SIFT"),
            ("Level 1", f"≥ {thresholds[1]}%", "#ff9800", "SIFT Selective"),
            ("Level 2", f"≥ {thresholds[2]}%", "#ff5722", "ORB"),
            ("Level 3", f"< {thresholds[2]}%", "#d32f2f", "FAST Critical")
        ]
        
        for level_name, battery, color, features in levels_info:
            level_frame = ctk.CTkFrame(self.config_content, fg_color="#2a2a2a", corner_radius=8)
            level_frame.pack(fill="x", pady=5)
            
            header = ctk.CTkFrame(level_frame, fg_color=color, corner_radius=6)
            header.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(header, text=level_name, font=("Roboto", 10, "bold"), text_color="white").pack(pady=5)
            
            info = ctk.CTkFrame(level_frame, fg_color="transparent")
            info.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(info, text=f"Battery: {battery}", font=("Roboto", 9)).pack(side="left")
            ctk.CTkLabel(info, text=f"Features: {features}", font=("Roboto", 9, "bold"), text_color="#00ff00").pack(side="right")
    
    def _show_metrics(self):
        """Show metrics display button"""
        self._clear_config_content()
        
        # Update button color
        for name, btn in self.config_tabs.items():
            color = "#ff9800" if name == 'metrics' else "#0066cc"
            btn.configure(fg_color=color)
        
        ctk.CTkLabel(
            self.config_content, text="Real-Time Metrics Display",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 10))
        
        info = ctk.CTkLabel(
            self.config_content,
            text="Open real-time graphs and metrics monitoring window\n"
                 "View training progress, loss curves, and action distribution\n\n"
                 "Data updates live during training",
            font=("Roboto", 10), text_color="#b0b0b0", justify="left"
        )
        info.pack(pady=30)
        
        ctk.CTkButton(
            self.config_content, text="📊 OPEN METRICS MONITOR",
            command=self._open_metrics_window, height=50,
            fg_color="#00aa66", hover_color="#007744",
            font=("Roboto", 12, "bold")
        ).pack(fill="x", pady=20)
    
    def _create_statistics_section(self, parent):
        """Create statistics panel"""
        
        frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=12)
        frame.pack(fill="both", expand=True)
        
        # Title
        ctk.CTkLabel(
            frame, text="📊 STATISTICS",
            font=("Roboto", 13, "bold"), text_color="#00ff00"
        ).pack(pady=12, padx=12, anchor="w")
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Create stat widgets
        self.stat_widgets = {}
        
        stats = [
            ("Episodes", "0", "#00ff00"),
            ("Avg Reward", "0.00", "#ffaa00"),
            ("Avg Loss", "0.000", "#ff6600"),
            ("Success Rate", "0%", "#00ccff"),
            ("Avg Uncertainty", "0.50", "#ff00ff"),
            ("Total Keyframes", "0", "#00ff00"),
            ("Battery Level", "100%", "#ffaa00"),
            ("Epsilon", "0.30", "#00ccff"),
        ]
        
        for title, value, color in stats:
            stat_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a", corner_radius=8)
            stat_frame.pack(fill="x", pady=6)
            
            ctk.CTkLabel(
                stat_frame, text=title, font=("Roboto", 9), text_color="#b0b0b0"
            ).pack(pady=(6, 2), padx=10, anchor="w")
            
            value_label = ctk.CTkLabel(
                stat_frame, text=value, font=("Roboto", 16, "bold"), text_color=color
            )
            value_label.pack(pady=(0, 6), padx=10, anchor="w")
            
            self.stat_widgets[title] = value_label
    
    def _create_param_slider(self, parent, label: str, min_val: float,
                            max_val: float, default: float, decimals: int = 2):
        """Create parameter slider"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        # Label and value
        label_row = ctk.CTkFrame(frame, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 4))
        
        ctk.CTkLabel(label_row, text=label, font=("Roboto", 9)).pack(side="left")
        value_label = ctk.CTkLabel(
            label_row, text=f"{default:.{decimals}f}", font=("Roboto", 9, "bold"),
            text_color="#00ff00"
        )
        value_label.pack(side="right")
        
        # Slider
        def on_change(value):
            rounded = round(float(value), decimals)
            value_label.configure(text=f"{rounded:.{decimals}f}")
        
        slider = ctk.CTkSlider(
            frame, from_=min_val, to=max_val, command=on_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        slider.pack(fill="x")
        slider.set(default)
    
    def _clear_config_content(self):
        """Clear configuration content"""
        for widget in self.config_content.winfo_children():
            widget.destroy()
    
    def _start_training(self):
        """Start training"""
        episodes = int(self.episodes_entry.get() or 500)
        
        self.backend.update_config({
            "episodes": episodes,
            "battery_profile": self.battery_var.get()
        })
        
        self.backend.start_training(episodes, on_progress=self._on_training_progress)
    
    def _pause_training(self):
        """Pause training"""
        self.backend.pause_training()
        self._update_status("PAUSED", "#ffaa00")
    
    def _stop_training(self):
        """Stop training"""
        self.backend.stop_training()
        self._update_status("STOPPED", "#ff4444")
    
    def _save_model(self):
        """Save model"""
        filepath = self.backend.save_model()
        print(f"✅ Model saved to {filepath}")
    
    def _load_model(self):
        """Load model"""
        # In production, would use file dialog
        self.backend.load_model("dqn_keyframe_model.pth")
    
    def _export_metrics(self):
        """Export metrics"""
        self.backend.export_metrics(format="json")
    
    def _on_training_progress(self, current: int, total: int):
        """Update training progress"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_text.configure(text=f"{current} / {total} episodes")
    
    def _on_episode_complete(self, metrics: Dict):
        """Update statistics when episode completes"""
        # This will be called by backend
        self._update_stat("Episodes", str(metrics.get("episode", 0)))
        self._update_stat("Avg Reward", f"{metrics.get('reward', 0):.2f}")
        self._update_stat("Avg Loss", f"{metrics.get('loss', 0):.4f}")
        self._update_stat("Success Rate", f"{metrics.get('success_rate', 0):.0f}%")
        self._update_stat("Avg Uncertainty", f"{metrics.get('uncertainty', 0):.3f}")
        self._update_stat("Total Keyframes", str(metrics.get('keyframes', 0)))
        self._update_stat("Battery Level", f"{metrics.get('battery', 100):.0f}%")
    
    def _on_training_start(self):
        """Handle training start"""
        self._update_status("TRAINING", "#00ff00")
    
    def _on_training_stop(self):
        """Handle training stop"""
        self._update_status("IDLE", "#ff4444")
    
    def _update_status(self, text: str, color: str):
        """Update status indicator"""
        self.status_text.configure(text=text, text_color=color)
        self.status_indicator.configure(text_color=color)
    
    def _update_stat(self, key: str, value: str):
        """Update statistic value"""
        if key in self.stat_widgets:
            self.stat_widgets[key].configure(text=value)
    
    def _open_reward_configurator(self):
        """Open reward configuration window"""
        def on_save(weights):
            self.backend.update_reward_weights(weights)
        
        configurator = RewardConfigurator(
            parent=self,
            on_save=on_save,
            initial_weights=self.backend.config.get("reward_weights", {})
        )
    
    def _open_degradation_configurator(self):
        """Open degradation configuration window"""
        def on_save(config):
            self.backend.update_battery_thresholds(config.get("thresholds", [60, 40, 20]))
        
        configurator = BatteryDegradationConfigurator(
            parent=self,
            on_save=on_save,
            initial_thresholds=self.backend.config.get("battery_thresholds", [60, 40, 20])
        )
    
    def _open_metrics_window(self):
        """Open metrics visualization window"""
        if self.metrics_window is None or not self.metrics_window.winfo_exists():
            self.metrics_window = RealtimeMetricsDisplay(self)
        else:
            self.metrics_window.lift()
    
    def _open_slam_viewer(self):
        """Open real SLAM visualization with live backend"""
        # Start integrated SLAM system if not running
        if not self.slam_running:
            self._start_slam_system()
        
        # Open viewer with active SLAM system
        if self.slam_viewer is None or not self.slam_viewer.winfo_exists():
            self.slam_viewer = RealSLAMViewer(
                parent=self,
                slam_system=self.slam_system,
                on_config_edit=self._open_slam_config_editor
            )
        else:
            self.slam_viewer.lift()
    
    def _start_slam_system(self):
        """Start the integrated SLAM system in background thread"""
        if self.slam_running:
            return
        
        if not IntegratedStereoSLAMSystem:
            from tkinter import messagebox
            messagebox.showerror("Error", "Could not import IntegratedStereoSLAMSystem")
            return
        
        try:
            left_url = self.slam_config.get('left_camera_url', 'http://192.168.1.100/stream')
            right_url = self.slam_config.get('right_camera_url', 'http://192.168.1.101/stream')
            
            print(f"\n🔴 Starting SLAM System")
            print(f"   Camera URLs configured:")
            print(f"   Left:  {left_url}")
            print(f"   Right: {right_url}")
            
            # Use adaptive camera manager (tries real, falls back to synthetic)
            camera_manager = AdaptiveCameraManager(left_url, right_url)
            
            # Create bare SLAM system (without integrated wrapper)
            self.slam_system = StereoSLAMSystem(max_keyframes=100)
            
            # Start camera in background
            self.slam_running = True
            self.slam_thread = threading.Thread(
                target=self._slam_with_adaptive_cameras,
                args=(camera_manager,),
                daemon=True
            )
            self.slam_thread.start()
            
            print("✅ SLAM system initialized and starting...")
        
        except Exception as e:
            print(f"❌ Error starting SLAM: {e}")
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("SLAM Error", f"Could not start SLAM system:\n{str(e)}")
            self.slam_running = False
    
    def _slam_with_adaptive_cameras(self, camera_manager):
        """Run SLAM with adaptive camera manager"""
        import time
        
        try:
            # Start camera (will try real, fallback to synthetic)
            if not camera_manager.start():
                print("❌ Failed to start camera")
                return
            
            print(f"\n📊 SLAM Processing Loop Starting")
            print(f"   Mode: {camera_manager.get_mode()}")
            print(f"   Processing at ~30 FPS")
            print("=" * 60)
            
            frame_count = 0
            while self.slam_running:
                try:
                    # Get stereo pair
                    stereo_pair = camera_manager.get_stereo_pair()
                    if stereo_pair is None:
                        time.sleep(0.01)
                        continue
                    
                    left_frame, right_frame = stereo_pair
                    
                    # Process with SLAM
                    is_keyframe = self.slam_system.process_stereo_pair(
                        left_frame, right_frame, timestamp=time.time()
                    )
                    
                    frame_count += 1
                    
                    # Print progress every 30 frames
                    if frame_count % 30 == 0:
                        kf_count = len(self.slam_system.keyframes) if hasattr(self.slam_system, 'keyframes') else 0
                        pc_count = len(self.slam_system.point_cloud) if (hasattr(self.slam_system, 'point_cloud') and 
                                                                          self.slam_system.point_cloud is not None) else 0
                        print(f"   Frames: {frame_count:4d} | Keyframes: {kf_count:3d} | Points: {pc_count:5d}")
                    
                    time.sleep(0.01)  # ~30 FPS
                
                except Exception as e:
                    print(f"Error in SLAM processing: {e}")
                    time.sleep(0.1)
        
        except Exception as e:
            print(f"❌ SLAM loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            camera_manager.stop()
            self.slam_running = False
            print("\n✅ SLAM Processing Stopped")
    
    def _open_slam_config_editor(self):
        """Open SLAM configuration editor"""
        from tkinter import messagebox
        messagebox.showinfo(
            "SLAM Configuration",
            "🔧 SLAM Configuration\n\n"
            "Connected to Real SLAM Backend:\n"
            "• Stereo vision calibration\n"
            "• Feature extraction (SIFT/ORB)\n"
            "• Visual odometry tracking\n"
            "• Loop closure detection\n"
            "• Bundle adjustment\n\n"
            "Current Backend:\n"
            "• StereoSLAMSystem (stereo_slam.py)\n"
            "• VisualOdometryEngine (visual_odometry.py)\n"
            "• CameraStreamHandler (camera_stream_handler.py)"
        )
    
    def _update_slam_viewer_data(self):
        """Update SLAM viewer with real backend data"""
        if self.slam_viewer is None or not self.slam_viewer.winfo_exists():
            return
        
        # The real SLAM viewer updates itself from the backend
        # through its processing thread. No manual updates needed.
    
    def _on_closing(self):
        """Handle window closing"""
        self.slam_running = False
        if self.slam_thread:
            self.slam_thread.join(timeout=2)
        self.backend.stop_training()
        if self.slam_viewer and self.slam_viewer.winfo_exists():
            self.slam_viewer.destroy()
        self.destroy()


if __name__ == "__main__":
    # Try to install customtkinter if needed
    try:
        import customtkinter
    except ImportError:
        print("Installing customtkinter...")
        import subprocess
        subprocess.check_call(["pip", "install", "customtkinter", "pillow"])
    
    app = AdvancedDQNTrainingDashboard()
    app.mainloop()
