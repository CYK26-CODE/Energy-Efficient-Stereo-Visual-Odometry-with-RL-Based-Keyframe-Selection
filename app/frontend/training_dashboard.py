#!/usr/bin/env python3
"""
CustomTkinter Frontend for DQN Training Dashboard
Real-time model performance monitoring, parameter configuration, and training control
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np
from typing import Dict, Callable, Optional
import threading
import json
from datetime import datetime


class ModernButton(ctk.CTkButton):
    """Enhanced button with modern styling"""
    def __init__(self, master, text: str, command: Callable = None, color: str = "#2E7D32",
                 text_color: str = "white", width: int = 150, height: int = 40, **kwargs):
        super().__init__(
            master, text=text, command=command,
            fg_color=color, text_color=text_color,
            width=width, height=height,
            font=("Roboto", 11, "bold"),
            corner_radius=8,
            hover_color=self._darker(color, 0.8),
            **kwargs
        )
    
    @staticmethod
    def _darker(hex_color: str, factor: float) -> str:
        """Make color darker"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return '#' + ''.join(f'{int(c * factor):02x}' for c in rgb)


class StatCard(ctk.CTkFrame):
    """Card widget for displaying statistics"""
    def __init__(self, master, title: str, value: str = "0.00", unit: str = "", **kwargs):
        super().__init__(master, fg_color="#1e1e1e", corner_radius=10, **kwargs)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, text=title, font=("Roboto", 12, "bold"),
            text_color="#b0b0b0"
        )
        self.title_label.pack(pady=(10, 5), padx=10)
        
        # Value
        self.value_label = ctk.CTkLabel(
            self, text=value, font=("Roboto", 24, "bold"),
            text_color="#00ff00"
        )
        self.value_label.pack(pady=(0, 5))
        
        # Unit
        self.unit_label = ctk.CTkLabel(
            self, text=unit, font=("Roboto", 10),
            text_color="#808080"
        )
        self.unit_label.pack(pady=(0, 10))
    
    def update_value(self, value: str, unit: str = ""):
        """Update displayed value"""
        self.value_label.configure(text=value)
        if unit:
            self.unit_label.configure(text=unit)


class ParameterSlider(ctk.CTkFrame):
    """Slider with label and value display"""
    def __init__(self, master, label: str, min_val: float, max_val: float,
                 default: float = None, callback: Callable = None, decimals: int = 3, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self.callback = callback
        
        # Label and value
        label_frame = ctk.CTkFrame(self, fg_color="transparent")
        label_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(label_frame, text=label, font=("Roboto", 11)).pack(side="left")
        
        self.value_label = ctk.CTkLabel(
            label_frame, text=f"{default:.{decimals}f}", font=("Roboto", 11, "bold"),
            text_color="#00ff00"
        )
        self.value_label.pack(side="right")
        
        # Slider
        self.slider = ctk.CTkSlider(
            self, from_=min_val, to=max_val,
            command=self._on_slider_change,
            progress_color="#00ff00",
            button_color="#00ff00"
        )
        self.slider.pack(fill="x")
        self.slider.set(default if default else min_val)
        
        self.current_value = default if default else min_val
    
    def _on_slider_change(self, value):
        """Handle slider change"""
        rounded_value = round(float(value), self.decimals)
        self.current_value = rounded_value
        self.value_label.configure(text=f"{rounded_value:.{self.decimals}f}")
        
        if self.callback:
            self.callback(rounded_value)
    
    def get(self) -> float:
        """Get current value"""
        return self.current_value
    
    def set(self, value: float):
        """Set slider value"""
        self.slider.set(value)


class DQNTrainingDashboard(ctk.CTk):
    """Main CustomTkinter application"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("DQN SLAM Training Dashboard")
        self.geometry("1600x1000")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        self.training_active = False
        self.training_thread = None
        self.metrics_history = {
            'rewards': [],
            'losses': [],
            'uncertainties': [],
            'episodes': [],
            'actions': [0, 0, 0]  # Count of each action
        }
        
        # Create main layout
        self._create_ui()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_ui(self):
        """Create main UI layout"""
        
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="#0a0a0a")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top header
        self._create_header(main_container)
        
        # Content area (2 columns)
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left column (camera feeds + maps)
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self._create_camera_panel(left_column)
        self._create_maps_panel(left_column)
        
        # Right column (stats + controls)
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True)
        
        self._create_performance_panel(right_column)
        self._create_config_panel(right_column)
        self._create_control_panel(right_column)
    
    def _create_header(self, parent):
        """Create header with title and indicators"""
        header = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=10, height=60)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        # Title
        ctk.CTkLabel(
            header, text="🤖 DQN SLAM TRAINING DASHBOARD",
            font=("Roboto", 20, "bold"), text_color="#00ff00"
        ).pack(side="left", padx=20, pady=15)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            header, text="● IDLE", font=("Roboto", 12, "bold"),
            text_color="#ff4444"
        )
        self.status_label.pack(side="right", padx=20, pady=15)
    
    def _create_camera_panel(self, parent):
        """Create camera feed panel"""
        camera_frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=10)
        camera_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            camera_frame, text="📷 CAMERA FEEDS",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(pady=10, padx=10, anchor="w")
        
        # Camera displays (placeholder)
        camera_display = ctk.CTkFrame(camera_frame, fg_color="#0a0a0a", height=200)
        camera_display.pack(fill="x", padx=10, pady=(0, 10))
        camera_display.pack_propagate(False)
        
        cameras_container = ctk.CTkFrame(camera_display, fg_color="transparent")
        cameras_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left camera
        left_cam = ctk.CTkFrame(cameras_container, fg_color="#2a2a2a", corner_radius=8)
        left_cam.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(left_cam, text="LEFT CAMERA", font=("Roboto", 10), text_color="#808080").pack(pady=30)
        ctk.CTkLabel(left_cam, text="[Video Stream]", text_color="#404040").pack(pady=40)
        
        # Right camera
        right_cam = ctk.CTkFrame(cameras_container, fg_color="#2a2a2a", corner_radius=8)
        right_cam.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(right_cam, text="RIGHT CAMERA", font=("Roboto", 10), text_color="#808080").pack(pady=30)
        ctk.CTkLabel(right_cam, text="[Video Stream]", text_color="#404040").pack(pady=40)
    
    def _create_maps_panel(self, parent):
        """Create 2D and 3D maps panel"""
        maps_frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=10)
        maps_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            maps_frame, text="🗺️ SLAM MAPS",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(pady=10, padx=10, anchor="w")
        
        maps_display = ctk.CTkFrame(maps_frame, fg_color="#0a0a0a")
        maps_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        maps_display.pack_propagate(False)
        
        maps_container = ctk.CTkFrame(maps_display, fg_color="transparent")
        maps_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 2D Map
        map_2d = ctk.CTkFrame(maps_container, fg_color="#2a2a2a", corner_radius=8)
        map_2d.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(map_2d, text="2D TOP-DOWN MAP", font=("Roboto", 10), text_color="#808080").pack(pady=30)
        ctk.CTkLabel(map_2d, text="[Trajectory Visualization]", text_color="#404040").pack(pady=40)
        
        # 3D Map
        map_3d = ctk.CTkFrame(maps_container, fg_color="#2a2a2a", corner_radius=8)
        map_3d.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(map_3d, text="3D POINT CLOUD", font=("Roboto", 10), text_color="#808080").pack(pady=30)
        ctk.CTkLabel(map_3d, text="[3D Map Visualization]", text_color="#404040").pack(pady=40)
    
    def _create_performance_panel(self, parent):
        """Create real-time performance statistics panel"""
        perf_frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=10)
        perf_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            perf_frame, text="📊 MODEL PERFORMANCE",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(pady=10, padx=10, anchor="w")
        
        # Stats grid
        stats_container = ctk.CTkFrame(perf_frame, fg_color="transparent")
        stats_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # Create stat cards in 2x3 grid
        self.stat_cards = {}
        
        stats_data = [
            ("Episode", "0", ""),
            ("Avg Reward", "0.00", ""),
            ("Avg Loss", "0.000", ""),
            ("Uncertainty", "0.50", ""),
            ("Success Rate", "0%", ""),
            ("Keyframes/Ep", "0", "")
        ]
        
        for i, (title, value, unit) in enumerate(stats_data):
            row = i // 3
            col = i % 3
            
            if col == 0:
                row_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
                row_frame.pack(fill="x", pady=5)
            
            card = StatCard(row_frame if col == 0 else row_frame, title, value, unit, width=100, height=70)
            card.pack(side="left", padx=5, fill="both", expand=True)
            
            self.stat_cards[title] = card
        
        # Progress bar for training
        ctk.CTkLabel(stats_container, text="Training Progress:", font=("Roboto", 10)).pack(pady=(10, 5), padx=10, anchor="w")
        self.progress_bar = ctk.CTkProgressBar(stats_container, value=0, height=8)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
    
    def _create_config_panel(self, parent):
        """Create model configuration panel"""
        config_frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=10)
        config_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            config_frame, text="⚙️ MODEL TRAINING PARAMETERS",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(pady=10, padx=10, anchor="w")
        
        # Scrollable frame for parameters
        config_scroll = ctk.CTkScrollableFrame(config_frame, fg_color="transparent")
        config_scroll.pack(fill="x", padx=10, pady=(0, 10))
        
        # DQN Parameters
        ctk.CTkLabel(config_scroll, text="DQN Hyperparameters", font=("Roboto", 10, "bold"), text_color="#ffaa00").pack(anchor="w", pady=(5, 10))
        
        self.param_lr = ParameterSlider(config_scroll, "Learning Rate", 1e-5, 1e-3, 1e-4, decimals=5)
        self.param_lr.pack(fill="x", pady=5)
        
        self.param_gamma = ParameterSlider(config_scroll, "Discount Factor (γ)", 0.9, 0.99, 0.99, decimals=3)
        self.param_gamma.pack(fill="x", pady=5)
        
        self.param_epsilon = ParameterSlider(config_scroll, "Exploration (ε)", 0.05, 0.5, 0.3, decimals=2)
        self.param_epsilon.pack(fill="x", pady=5)
        
        self.param_batch_size = ParameterSlider(config_scroll, "Batch Size", 16, 256, 64, decimals=0)
        self.param_batch_size.pack(fill="x", pady=5)
        
        # Reward Weights
        ctk.CTkLabel(config_scroll, text="Reward Weights", font=("Roboto", 10, "bold"), text_color="#ffaa00").pack(anchor="w", pady=(15, 10))
        
        self.param_w_benefit = ParameterSlider(config_scroll, "Localization Weight (w_b)", 1.0, 20.0, 8.0, decimals=1)
        self.param_w_benefit.pack(fill="x", pady=5)
        
        self.param_w_energy = ParameterSlider(config_scroll, "Energy Weight (w_e)", 1.0, 20.0, 6.0, decimals=1)
        self.param_w_energy.pack(fill="x", pady=5)
        
        self.param_w_loss = ParameterSlider(config_scroll, "Tracking Loss Weight (w_l)", 10.0, 100.0, 40.0, decimals=1)
        self.param_w_loss.pack(fill="x", pady=5)
        
        self.param_w_step = ParameterSlider(config_scroll, "Step Penalty (w_t)", 0.001, 0.1, 0.01, decimals=3)
        self.param_w_step.pack(fill="x", pady=5)
    
    def _create_control_panel(self, parent):
        """Create training control panel"""
        control_frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=10)
        control_frame.pack(fill="x")
        
        ctk.CTkLabel(
            control_frame, text="🎮 TRAINING CONTROLS",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(pady=10, padx=10, anchor="w")
        
        # Episode control
        episode_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        episode_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(episode_frame, text="Episodes:", font=("Roboto", 10)).pack(side="left", padx=(0, 10))
        self.episode_entry = ctk.CTkEntry(episode_frame, width=100, placeholder_text="500")
        self.episode_entry.pack(side="left", padx=5)
        self.episode_entry.insert(0, "500")
        
        # Battery profile selection
        battery_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        battery_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(battery_frame, text="Battery Profile:", font=("Roboto", 10)).pack(side="left", padx=(0, 10))
        self.battery_profile_var = ctk.StringVar(value="declining")
        battery_options = ctk.CTkOptionMenu(
            battery_frame, values=["constant", "declining", "variable"],
            variable=self.battery_profile_var, width=120
        )
        battery_options.pack(side="left", padx=5)
        
        # Training buttons
        buttons_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=(10, 10))
        
        self.start_btn = ModernButton(buttons_frame, "▶ START TRAINING", command=self._start_training, color="#2E7D32")
        self.start_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.pause_btn = ModernButton(buttons_frame, "⏸ PAUSE", command=self._pause_training, color="#ff6600")
        self.pause_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.stop_btn = ModernButton(buttons_frame, "⏹ STOP", command=self._stop_training, color="#d32f2f")
        self.stop_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Save/Load buttons
        save_load_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        save_load_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.save_btn = ModernButton(save_load_frame, "💾 SAVE MODEL", command=self._save_model, color="#0066cc")
        self.save_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.load_btn = ModernButton(save_load_frame, "📂 LOAD MODEL", command=self._load_model, color="#0066cc")
        self.load_btn.pack(side="left", padx=5, fill="x", expand=True)
    
    def _start_training(self):
        """Start training"""
        if not self.training_active:
            self.training_active = True
            self.status_label.configure(text="● TRAINING", text_color="#00ff00")
            self.start_btn.configure(state="disabled", fg_color="#666666")
            
            # Get parameters
            episodes = int(self.episode_entry.get() or 500)
            
            # Start training in thread
            self.training_thread = threading.Thread(
                target=self._training_loop,
                args=(episodes,),
                daemon=True
            )
            self.training_thread.start()
    
    def _pause_training(self):
        """Pause training"""
        self.training_active = False
        self.status_label.configure(text="● PAUSED", text_color="#ffaa00")
        self.start_btn.configure(state="normal", fg_color="#2E7D32")
    
    def _stop_training(self):
        """Stop training"""
        self.training_active = False
        self.status_label.configure(text="● IDLE", text_color="#ff4444")
        self.start_btn.configure(state="normal", fg_color="#2E7D32")
        self.progress_bar.set(0)
    
    def _training_loop(self, episodes: int):
        """Simulate training loop"""
        for episode in range(episodes):
            if not self.training_active:
                break
            
            # Simulate training
            reward = np.random.uniform(20, 60) + (episode / episodes) * 30
            loss = max(0.001, 0.5 - (episode / episodes) * 0.4)
            uncertainty = max(0.2, 0.7 - (episode / episodes) * 0.3)
            success_rate = 70 + (episode / episodes) * 25
            
            # Update metrics
            self.metrics_history['rewards'].append(reward)
            self.metrics_history['losses'].append(loss)
            self.metrics_history['uncertainties'].append(uncertainty)
            self.metrics_history['episodes'].append(episode)
            
            # Update UI
            avg_reward = np.mean(self.metrics_history['rewards'][-20:])
            avg_loss = np.mean(self.metrics_history['losses'][-20:])
            
            self.stat_cards["Episode"].update_value(str(episode))
            self.stat_cards["Avg Reward"].update_value(f"{avg_reward:.2f}")
            self.stat_cards["Avg Loss"].update_value(f"{avg_loss:.4f}")
            self.stat_cards["Uncertainty"].update_value(f"{uncertainty:.3f}")
            self.stat_cards["Success Rate"].update_value(f"{success_rate:.0f}%")
            
            progress = (episode + 1) / episodes
            self.progress_bar.set(progress)
            
            self.update()
            
            # Simulate step delay
            import time
            time.sleep(0.1)
        
        self.training_active = False
        self.status_label.configure(text="● COMPLETED", text_color="#00ff00")
        self.start_btn.configure(state="normal", fg_color="#2E7D32")
    
    def _save_model(self):
        """Save model (placeholder)"""
        print("Model saved!")
    
    def _load_model(self):
        """Load model (placeholder)"""
        print("Model loaded!")
    
    def _on_closing(self):
        """Handle window closing"""
        self.training_active = False
        self.destroy()


if __name__ == "__main__":
    # Install customtkinter if needed
    try:
        import customtkinter
    except ImportError:
        print("Installing customtkinter...")
        import subprocess
        subprocess.check_call(["pip", "install", "customtkinter"])
    
    app = DQNTrainingDashboard()
    app.mainloop()
