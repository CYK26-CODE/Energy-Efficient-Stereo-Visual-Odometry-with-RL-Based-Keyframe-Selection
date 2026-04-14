#!/usr/bin/env python3
"""
Reward Weight Configuration Panel
Allows real-time adjustment of DQN reward parameters with visual feedback
"""

import customtkinter as ctk
from typing import Callable, Dict, Optional
import json
from datetime import datetime


class RewardVisualization(ctk.CTkFrame):
    """Visual representation of reward weights"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#2a2a2a", corner_radius=10, **kwargs)
        
        # Title
        ctk.CTkLabel(
            self, text="Reward Composition",
            font=("Roboto", 11, "bold"), text_color="#00ff00"
        ).pack(pady=10, anchor="w", padx=10)
        
        # Weights display
        self.weights_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.weights_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.weight_labels = {}
    
    def update_weights(self, weights: Dict[str, float]):
        """Update weight display"""
        # Clear previous labels
        for widget in self.weights_frame.winfo_children():
            widget.destroy()
        
        total = sum(weights.values())
        
        for name, value in weights.items():
            # Calculate percentage
            pct = (value / total * 100) if total > 0 else 0
            
            # Weight bar frame
            bar_container = ctk.CTkFrame(self.weights_frame, fg_color="transparent")
            bar_container.pack(fill="x", pady=3)
            
            # Label
            ctk.CTkLabel(
                bar_container, text=f"{name}:",
                font=("Roboto", 9), text_color="#b0b0b0", width=40
            ).pack(side="left", padx=(0, 5))
            
            # Progress bar
            bar = ctk.CTkProgressBar(bar_container, value=pct/100, height=8)
            bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            # Percentage
            ctk.CTkLabel(
                bar_container, text=f"{pct:.1f}%",
                font=("Roboto", 9, "bold"), text_color="#00ff00", width=50
            ).pack(side="right")


class RewardPreset(ctk.CTkFrame):
    """Preset configurations"""
    
    def __init__(self, master, on_apply: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        ctk.CTkLabel(
            self, text="Quick Presets",
            font=("Roboto", 11, "bold"), text_color="#00ff00"
        ).pack(pady=5, anchor="w")
        
        preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        preset_frame.pack(fill="x", pady=5)
        
        self.presets = {
            "Conservative": {"w_b": 12.0, "w_e": 10.0, "w_l": 50.0, "w_t": 0.02},
            "Balanced": {"w_b": 8.0, "w_e": 6.0, "w_l": 40.0, "w_t": 0.01},
            "Aggressive": {"w_b": 4.0, "w_e": 2.0, "w_l": 30.0, "w_t": 0.005}
        }
        
        for preset_name, values in self.presets.items():
            btn = ctk.CTkButton(
                preset_frame, text=preset_name,
                command=lambda v=values: on_apply(v),
                fg_color="#0066cc", hover_color="#0052a3",
                font=("Roboto", 9, "bold")
            )
            btn.pack(side="left", fill="both", expand=True, padx=3, pady=5)


class RewardConfigurator(ctk.CTkToplevel):
    """Standalone reward configuration window"""
    
    def __init__(self, parent=None, on_save: Callable = None, initial_weights: Dict = None):
        super().__init__(parent)
        
        self.title("Reward Weight Configuration")
        self.geometry("600x800")
        self.resizable(False, False)
        
        # Center window on parent
        if parent:
            self.transient(parent)
            self.grab_set()
        
        self.on_save = on_save
        self.weights = initial_weights or {
            "w_b": 8.0, "w_e": 6.0, "w_l": 40.0, "w_t": 0.01
        }
        
        # Configure appearance
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
            header, text="⚖️ REWARD WEIGHT CONFIGURATION",
            font=("Roboto", 14, "bold"), text_color="#00ff00"
        ).pack(pady=15, padx=15, anchor="w")
        
        # Description
        desc = ctk.CTkLabel(
            main_frame,
            text="Adjust weights to shape agent behavior:\n"
                 "• w_b: Localization accuracy reward\n"
                 "• w_e: Energy consumption penalty (battery-aware)\n"
                 "• w_l: Tracking loss penalty\n"
                 "• w_t: Per-step penalty (exploration cost)",
            font=("Roboto", 10), text_color="#b0b0b0", justify="left"
        )
        desc.pack(fill="x", pady=(0, 15))
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Weight sliders
        sliders_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        sliders_frame.pack(fill="x", pady=(0, 15))
        
        self.sliders = {}
        
        # Localization weight (w_b)
        ctk.CTkLabel(
            sliders_frame, text="Localization Weight (w_b)",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.w_b_label = ctk.CTkLabel(
            sliders_frame, text=f"Value: {self.weights['w_b']:.2f}",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.w_b_label.pack(anchor="w", pady=(0, 3))
        
        self.w_b_slider = ctk.CTkSlider(
            sliders_frame, from_=1, to=20, command=self._on_w_b_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.w_b_slider.pack(fill="x", pady=(0, 10))
        self.w_b_slider.set(self.weights['w_b'])
        
        # Energy weight (w_e)
        ctk.CTkLabel(
            sliders_frame, text="Energy Weight (w_e)",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.w_e_label = ctk.CTkLabel(
            sliders_frame, text=f"Value: {self.weights['w_e']:.2f}",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.w_e_label.pack(anchor="w", pady=(0, 3))
        
        self.w_e_slider = ctk.CTkSlider(
            sliders_frame, from_=1, to=20, command=self._on_w_e_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.w_e_slider.pack(fill="x", pady=(0, 10))
        self.w_e_slider.set(self.weights['w_e'])
        
        # Tracking loss weight (w_l)
        ctk.CTkLabel(
            sliders_frame, text="Tracking Loss Weight (w_l)",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.w_l_label = ctk.CTkLabel(
            sliders_frame, text=f"Value: {self.weights['w_l']:.2f}",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.w_l_label.pack(anchor="w", pady=(0, 3))
        
        self.w_l_slider = ctk.CTkSlider(
            sliders_frame, from_=10, to=100, command=self._on_w_l_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.w_l_slider.pack(fill="x", pady=(0, 10))
        self.w_l_slider.set(self.weights['w_l'])
        
        # Step penalty (w_t)
        ctk.CTkLabel(
            sliders_frame, text="Step Penalty (w_t)",
            font=("Roboto", 11, "bold"), text_color="#ffaa00"
        ).pack(anchor="w", pady=(10, 5))
        
        self.w_t_label = ctk.CTkLabel(
            sliders_frame, text=f"Value: {self.weights['w_t']:.4f}",
            font=("Roboto", 10), text_color="#00ff00"
        )
        self.w_t_label.pack(anchor="w", pady=(0, 3))
        
        self.w_t_slider = ctk.CTkSlider(
            sliders_frame, from_=0.001, to=0.1, command=self._on_w_t_change,
            progress_color="#00ff00", button_color="#00ff00"
        )
        self.w_t_slider.pack(fill="x", pady=(0, 15))
        self.w_t_slider.set(self.weights['w_t'])
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Visualization
        self.visualization = RewardVisualization(main_frame)
        self.visualization.pack(fill="x", pady=(0, 15))
        self._update_visualization()
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Presets
        preset_panel = RewardPreset(main_frame, self._apply_preset)
        preset_panel.pack(fill="x", pady=(0, 15))
        
        # Divider
        ctk.CTkFrame(main_frame, fg_color="#333333").pack(fill="x", pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 0))
        
        ctk.CTkButton(
            button_frame, text="💾 SAVE & APPLY",
            command=self._save_weights,
            fg_color="#2E7D32", hover_color="#1b5620",
            font=("Roboto", 11, "bold"), height=40
        ).pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            button_frame, text="↺ RESET TO DEFAULT",
            command=self._reset_weights,
            fg_color="#0066cc", hover_color="#004499",
            font=("Roboto", 11, "bold"), height=40
        ).pack(side="right", fill="both", expand=True, padx=(5, 0))
    
    def _on_w_b_change(self, value):
        """Handle localization weight change"""
        self.weights['w_b'] = round(float(value), 2)
        self.w_b_label.configure(text=f"Value: {self.weights['w_b']:.2f}")
        self._update_visualization()
    
    def _on_w_e_change(self, value):
        """Handle energy weight change"""
        self.weights['w_e'] = round(float(value), 2)
        self.w_e_label.configure(text=f"Value: {self.weights['w_e']:.2f}")
        self._update_visualization()
    
    def _on_w_l_change(self, value):
        """Handle tracking loss weight change"""
        self.weights['w_l'] = round(float(value), 2)
        self.w_l_label.configure(text=f"Value: {self.weights['w_l']:.2f}")
        self._update_visualization()
    
    def _on_w_t_change(self, value):
        """Handle step penalty change"""
        self.weights['w_t'] = round(float(value), 4)
        self.w_t_label.configure(text=f"Value: {self.weights['w_t']:.4f}")
        self._update_visualization()
    
    def _update_visualization(self):
        """Update weight visualization"""
        self.visualization.update_weights(self.weights)
    
    def _apply_preset(self, preset: Dict):
        """Apply preset weights"""
        self.weights = preset.copy()
        self.w_b_slider.set(self.weights['w_b'])
        self.w_e_slider.set(self.weights['w_e'])
        self.w_l_slider.set(self.weights['w_l'])
        self.w_t_slider.set(self.weights['w_t'])
        self._update_visualization()
    
    def _reset_weights(self):
        """Reset to default weights"""
        self._apply_preset({
            "w_b": 8.0, "w_e": 6.0, "w_l": 40.0, "w_t": 0.01
        })
    
    def _save_weights(self):
        """Save and apply weights"""
        if self.on_save:
            self.on_save(self.weights)
        
        print(f"✅ Reward weights saved: {self.weights}")
        self.destroy()
    
    def get_weights(self) -> Dict:
        """Get current weights"""
        return self.weights.copy()


if __name__ == "__main__":
    def test_save(weights):
        print(f"Saved weights: {weights}")
    
    root = ctk.CTk()
    root.withdraw()
    
    configurator = RewardConfigurator(root, on_save=test_save)
    root.mainloop()
