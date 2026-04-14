#!/usr/bin/env python3
"""
Battery Degradation Level Configuration Panel
Manage 4-level battery thresholds and per-level SLAM strategy configuration
"""

import customtkinter as ctk
from typing import Callable, Dict, List, Optional
import json


class DegradationLevelCard(ctk.CTkFrame):
    """Display configuration for one degradation level"""
    
    def __init__(self, master, level: int, battery_threshold: float, color: str,
                 feature_type: str, descriptor_retention: float,
                 keyframe_freq: str, **kwargs):
        super().__init__(master, fg_color="#1e1e1e", corner_radius=10, **kwargs)
        
        self.level = level
        
        # Header
        header = ctk.CTkFrame(self, fg_color=color, corner_radius=8)
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            header, text=f"Level {level}",
            font=("Roboto", 12, "bold"), text_color="white"
        ).pack(pady=8)
        
        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Battery threshold
        self._add_info_row(content, "Battery Threshold", f"≥ {battery_threshold}%")
        
        # Feature type
        self._add_info_row(content, "Feature Type", feature_type)
        
        # Descriptor retention
        self._add_info_row(content, "Descriptor Retention", f"{descriptor_retention:.0f}%")
        
        # Keyframe frequency
        self._add_info_row(content, "Keyframe Frequency", keyframe_freq)
    
    def _add_info_row(self, parent, label: str, value: str):
        """Add info row"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        
        ctk.CTkLabel(
            row, text=label + ":",
            font=("Roboto", 9), text_color="#b0b0b0"
        ).pack(side="left", anchor="w")
        
        ctk.CTkLabel(
            row, text=value,
            font=("Roboto", 9, "bold"), text_color="#00ff00"
        ).pack(side="right", anchor="e")


class BatteryDegradationConfigurator(ctk.CTkToplevel):
    """Standalone battery degradation configuration window"""
    
    def __init__(self, parent=None, on_save: Callable = None, 
                 initial_thresholds: List[float] = None):
        super().__init__(parent)
        
        self.title("Battery Degradation Configuration")
        self.geometry("700x900")
        self.resizable(False, False)
        
        # Center on parent
        if parent:
            self.transient(parent)
            self.grab_set()
        
        self.on_save = on_save
        
        # Default thresholds: L0≥60%, L1≥40%, L2≥20%, L3<20%
        self.thresholds = initial_thresholds or [60, 40, 20]
        
        # Level configurations
        self.level_configs = {
            0: {"color": "#2E7D32", "features": "SIFT", "retention": 100, "freq": "Frequent"},
            1: {"color": "#ff9800", "features": "SIFT", "retention": 80, "freq": "Moderate"},
            2: {"color": "#ff5722", "features": "ORB", "retention": 50, "freq": "Rare"},
            3: {"color": "#d32f2f", "features": "FAST", "retention": 20, "freq": "Critical"}
        }
        
        ctk.set_appearance_mode("dark")
        self._create_ui()
    
    def _create_ui(self):
        """Create UI elements"""
        
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=10)
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            header, text="🔋 BATTERY DEGRADATION CONFIGURATION",
            font=("Roboto", 14, "bold"), text_color="#00ff00"
        ).pack(pady=15, padx=15, anchor="w")
        
        # Description
        desc = ctk.CTkLabel(
            main_frame,
            text="Configure battery thresholds and SLAM strategy for each degradation level.\n"
                 "Lower battery triggers more aggressive feature reduction and less frequent keyframes.",
            font=("Roboto", 10), text_color="#b0b0b0", justify="left"
        )
        desc.pack(fill="x", pady=(0, 15))
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Scrollable frame for sliders
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Threshold sliders
        ctk.CTkLabel(
            scroll_frame, text="Battery Thresholds",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(anchor="w", pady=(10, 15))
        
        self.threshold_labels = {}
        self.threshold_sliders = {}
        
        # Level 0 threshold (≥60%)
        ctk.CTkLabel(
            scroll_frame, text="Level 0 → Level 1 Threshold (L0 ≥ T0)",
            font=("Roboto", 10, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.threshold_labels['L0'] = ctk.CTkLabel(
            scroll_frame, text=f"Current: {self.thresholds[0]}%",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.threshold_labels['L0'].pack(anchor="w", pady=(0, 3))
        
        self.threshold_sliders['L0'] = ctk.CTkSlider(
            scroll_frame, from_=40, to=100, command=self._on_t0_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.threshold_sliders['L0'].pack(fill="x", pady=(0, 15))
        self.threshold_sliders['L0'].set(self.thresholds[0])
        
        # Level 1 threshold (≥40%)
        ctk.CTkLabel(
            scroll_frame, text="Level 1 → Level 2 Threshold (L1 ≥ T1)",
            font=("Roboto", 10, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.threshold_labels['L1'] = ctk.CTkLabel(
            scroll_frame, text=f"Current: {self.thresholds[1]}%",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.threshold_labels['L1'].pack(anchor="w", pady=(0, 3))
        
        self.threshold_sliders['L1'] = ctk.CTkSlider(
            scroll_frame, from_=20, to=self.thresholds[0]-5, command=self._on_t1_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.threshold_sliders['L1'].pack(fill="x", pady=(0, 15))
        self.threshold_sliders['L1'].set(self.thresholds[1])
        
        # Level 2 threshold (≥20%)
        ctk.CTkLabel(
            scroll_frame, text="Level 2 → Level 3 Threshold (L2 ≥ T2)",
            font=("Roboto", 10, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.threshold_labels['L2'] = ctk.CTkLabel(
            scroll_frame, text=f"Current: {self.thresholds[2]}%",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.threshold_labels['L2'].pack(anchor="w", pady=(0, 3))
        
        self.threshold_sliders['L2'] = ctk.CTkSlider(
            scroll_frame, from_=5, to=self.thresholds[1]-5, command=self._on_t2_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.threshold_sliders['L2'].pack(fill="x", pady=(0, 15))
        self.threshold_sliders['L2'].set(self.thresholds[2])
        
        # Divider
        ctk.CTkFrame(scroll_frame, fg_color="#333333").pack(fill="x", pady=15)
        
        # Level configurations display
        ctk.CTkLabel(
            scroll_frame, text="Level Configurations",
            font=("Roboto", 12, "bold"), text_color="#00ff00"
        ).pack(anchor="w", pady=(10, 15))
        
        # Level 0
        DegradationLevelCard(
            scroll_frame, 0, self.thresholds[0], "#2E7D32",
            "SIFT", 100, "Frequent (Full BA)"
        ).pack(fill="x", pady=5)
        
        # Level 1
        DegradationLevelCard(
            scroll_frame, 1, self.thresholds[1], "#ff9800",
            "SIFT", 80, "Moderate (Selective BA)"
        ).pack(fill="x", pady=5)
        
        # Level 2
        DegradationLevelCard(
            scroll_frame, 2, self.thresholds[2], "#ff5722",
            "ORB", 50, "Rare (No IMU)"
        ).pack(fill="x", pady=5)
        
        # Level 3
        DegradationLevelCard(
            scroll_frame, 3, 0, "#d32f2f",
            "FAST", 20, "Critical (Minimal)"
        ).pack(fill="x", pady=5)
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Presets
        preset_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        preset_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            preset_frame, text="Quick Presets",
            font=("Roboto", 11, "bold"), text_color="#00ff00"
        ).pack(anchor="w", pady=5)
        
        preset_buttons = ctk.CTkFrame(preset_frame, fg_color="transparent")
        preset_buttons.pack(fill="x", pady=(5, 0))
        
        ctk.CTkButton(
            preset_buttons, text="Conservative",
            command=lambda: self._apply_preset([70, 50, 25]),
            fg_color="#0066cc", hover_color="#0052a3",
            font=("Roboto", 9, "bold"), height=30
        ).pack(side="left", fill="both", expand=True, padx=(0, 3))
        
        ctk.CTkButton(
            preset_buttons, text="Balanced",
            command=lambda: self._apply_preset([60, 40, 20]),
            fg_color="#0066cc", hover_color="#0052a3",
            font=("Roboto", 9, "bold"), height=30
        ).pack(side="left", fill="both", expand=True, padx=3)
        
        ctk.CTkButton(
            preset_buttons, text="Aggressive",
            command=lambda: self._apply_preset([50, 30, 15]),
            fg_color="#0066cc", hover_color="#0052a3",
            font=("Roboto", 9, "bold"), height=30
            ).pack(side="right", fill="both", expand=True, padx=(3, 0))
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(
            button_frame, text="💾 SAVE & APPLY",
            command=self._save_config,
            fg_color="#2E7D32", hover_color="#1b5620",
            font=("Roboto", 11, "bold"), height=40
        ).pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            button_frame, text="↺ RESET TO DEFAULT",
            command=lambda: self._apply_preset([60, 40, 20]),
            fg_color="#0066cc", hover_color="#004499",
            font=("Roboto", 11, "bold"), height=40
        ).pack(side="right", fill="both", expand=True, padx=(5, 0))
    
    def _on_t0_change(self, value):
        """Handle Level 0 threshold change"""
        self.thresholds[0] = int(float(value))
        # Ensure T0 > T1
        if self.thresholds[0] <= self.thresholds[1]:
            self.thresholds[1] = max(self.thresholds[0] - 10, 0)
            self.threshold_sliders['L1'].set(self.thresholds[1])
        
        self.threshold_labels['L0'].configure(
            text=f"Current: {self.thresholds[0]}%"
        )
        self.threshold_sliders['L1'].configure(to=self.thresholds[0] - 5)
    
    def _on_t1_change(self, value):
        """Handle Level 1 threshold change"""
        self.thresholds[1] = int(float(value))
        # Ensure T1 > T2
        if self.thresholds[1] <= self.thresholds[2]:
            self.thresholds[2] = max(self.thresholds[1] - 10, 0)
            self.threshold_sliders['L2'].set(self.thresholds[2])
        
        self.threshold_labels['L1'].configure(
            text=f"Current: {self.thresholds[1]}%"
        )
        self.threshold_sliders['L2'].configure(to=self.thresholds[1] - 5)
    
    def _on_t2_change(self, value):
        """Handle Level 2 threshold change"""
        self.thresholds[2] = int(float(value))
        self.threshold_labels['L2'].configure(
            text=f"Current: {self.thresholds[2]}%"
        )
    
    def _apply_preset(self, thresholds: List[float]):
        """Apply preset thresholds"""
        self.thresholds = list(thresholds)
        self.threshold_sliders['L0'].set(self.thresholds[0])
        self.threshold_sliders['L1'].set(self.thresholds[1])
        self.threshold_sliders['L2'].set(self.thresholds[2])
        
        self.threshold_labels['L0'].configure(text=f"Current: {self.thresholds[0]}%")
        self.threshold_labels['L1'].configure(text=f"Current: {self.thresholds[1]}%")
        self.threshold_labels['L2'].configure(text=f"Current: {self.thresholds[2]}%")
    
    def _save_config(self):
        """Save configuration"""
        config = {
            "thresholds": self.thresholds,
            "level_configs": self.level_configs
        }
        
        if self.on_save:
            self.on_save(config)
        
        print(f"✅ Battery degradation saved: {self.thresholds}")
        self.destroy()
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return {
            "thresholds": self.thresholds.copy(),
            "level_configs": self.level_configs.copy()
        }


if __name__ == "__main__":
    def test_save(config):
        print(f"Saved config: {config}")
    
    root = ctk.CTk()
    root.withdraw()
    
    configurator = BatteryDegradationConfigurator(root, on_save=test_save)
    root.mainloop()
