#!/usr/bin/env python3
"""
Real-time Performance Monitoring and Visualization
Displays training metrics, graphs, and statistics in real-time
"""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import List, Dict
from collections import deque
import json


class RealtimeMetricsDisplay(ctk.CTkToplevel):
    """Real-time metrics visualization window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.title("Real-time Training Metrics")
        self.geometry("1000x700")
        
        if parent:
            self.transient(parent)
        
        # Data storage (circular buffers)
        self.max_points = 100  # Keep last 100 data points
        self.rewards = deque(maxlen=self.max_points)
        self.losses = deque(maxlen=self.max_points)
        self.uncertainties = deque(maxlen=self.max_points)
        self.episodes = deque(maxlen=self.max_points)
        self.actions_dist = [0, 0, 0]  # Skip, Save Normal, Save Light
        
        ctk.set_appearance_mode("dark")
        self._create_ui()
        
        # Start update loop
        self.update_count = 0
    
    def _create_ui(self):
        """Create visualization UI"""
        
        main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header = ctk.CTkLabel(
            main_frame, text="📊 REAL-TIME TRAINING METRICS",
            font=("Roboto", 14, "bold"), text_color="#00ff00"
        )
        header.pack(pady=(0, 10))
        
        # Create matplotlib figure with 4 subplots
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor="#0a0a0a", edgecolor="#333333")
        self.fig.patch.set_alpha(0.9)
        
        # Reward plot
        self.ax_reward = self.fig.add_subplot(2, 2, 1)
        self.ax_reward.set_title("Episode Rewards", color="#00ff00", fontsize=10, fontweight="bold")
        self.ax_reward.set_facecolor("#1a1a1a")
        self.ax_reward.grid(True, alpha=0.2, color="#444444")
        self.line_reward, = self.ax_reward.plot([], [], color="#00ff00", linewidth=2)
        
        # Loss plot
        self.ax_loss = self.fig.add_subplot(2, 2, 2)
        self.ax_loss.set_title("Training Loss", color="#ff6600", fontsize=10, fontweight="bold")
        self.ax_loss.set_facecolor("#1a1a1a")
        self.ax_loss.grid(True, alpha=0.2, color="#444444")
        self.line_loss, = self.ax_loss.plot([], [], color="#ff6600", linewidth=2)
        
        # Uncertainty plot
        self.ax_unc = self.fig.add_subplot(2, 2, 3)
        self.ax_unc.set_title("Localization Uncertainty", color="#00ccff", fontsize=10, fontweight="bold")
        self.ax_unc.set_facecolor("#1a1a1a")
        self.ax_unc.grid(True, alpha=0.2, color="#444444")
        self.line_unc, = self.ax_unc.plot([], [], color="#00ccff", linewidth=2)
        
        # Action distribution (bar chart)
        self.ax_actions = self.fig.add_subplot(2, 2, 4)
        self.ax_actions.set_title("Action Distribution", color="#ff00ff", fontsize=10, fontweight="bold")
        self.ax_actions.set_facecolor("#1a1a1a")
        self.ax_actions.set_xticks([0, 1, 2])
        self.ax_actions.set_xticklabels(["SKIP", "NORMAL", "LIGHT"], color="#b0b0b0", fontsize=9)
        self.bars = self.ax_actions.bar([0, 1, 2], [0, 0, 0], color=["#00ff00", "#00ccff", "#ff6600"])
        
        # Adjust layout
        self.fig.tight_layout()
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, main_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Bottom info frame
        info_frame = ctk.CTkFrame(main_frame, fg_color="#1e1e1e", corner_radius=10)
        info_frame.pack(fill="x", pady=(10, 0))
        
        # Status labels
        status_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_container.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            status_container, text="Episodes:", font=("Roboto", 10, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.label_episodes = ctk.CTkLabel(
            status_container, text="0", font=("Roboto", 10), text_color="#00ff00"
        )
        self.label_episodes.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            status_container, text="Avg Reward:", font=("Roboto", 10, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.label_avg_reward = ctk.CTkLabel(
            status_container, text="0.00", font=("Roboto", 10), text_color="#00ff00"
        )
        self.label_avg_reward.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            status_container, text="Avg Loss:", font=("Roboto", 10, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.label_avg_loss = ctk.CTkLabel(
            status_container, text="0.000", font=("Roboto", 10), text_color="#ff6600"
        )
        self.label_avg_loss.pack(side="left")
    
    def add_episode_data(self, reward: float, loss: float, uncertainty: float,
                        actions: List[int] = None):
        """Add episode data point"""
        self.rewards.append(reward)
        self.losses.append(loss)
        self.uncertainties.append(uncertainty)
        self.episodes.append(len(self.episodes))
        
        if actions:
            self.actions_dist = [int(a) for a in actions]
        
        # Update labels
        self.label_episodes.configure(text=str(len(self.episodes)))
        
        if self.rewards:
            avg_reward = np.mean(list(self.rewards))
            self.label_avg_reward.configure(text=f"{avg_reward:.2f}")
        
        if self.losses:
            avg_loss = np.mean(list(self.losses))
            self.label_avg_loss.configure(text=f"{avg_loss:.4f}")
        
        self.update_count += 1
        
        # Update plots every 5 data points
        if self.update_count % 5 == 0:
            self._update_plots()
    
    def _update_plots(self):
        """Update all plots"""
        x = list(range(len(self.episodes)))
        
        # Update reward plot
        if len(x) > 0:
            self.line_reward.set_data(x, list(self.rewards))
            self.ax_reward.relim()
            self.ax_reward.autoscale_view()
        
        # Update loss plot
        if len(x) > 0:
            self.line_loss.set_data(x, list(self.losses))
            self.ax_loss.relim()
            self.ax_loss.autoscale_view()
        
        # Update uncertainty plot
        if len(x) > 0:
            self.line_unc.set_data(x, list(self.uncertainties))
            self.ax_unc.relim()
            self.ax_unc.autoscale_view()
        
        # Update action distribution
        total = sum(self.actions_dist) if sum(self.actions_dist) > 0 else 1
        percentages = [a / total * 100 for a in self.actions_dist]
        
        for bar, height in zip(self.bars, percentages):
            bar.set_height(height)
        
        self.ax_actions.set_ylim([0, max(percentages + [10])])
        
        # Refresh canvas
        self.canvas.draw_idle()
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        return {
            "episodes": len(self.episodes),
            "avg_reward": float(np.mean(list(self.rewards))) if self.rewards else 0,
            "avg_loss": float(np.mean(list(self.losses))) if self.losses else 0,
            "avg_uncertainty": float(np.mean(list(self.uncertainties))) if self.uncertainties else 0,
            "action_distribution": self.actions_dist
        }


class MetricsExporter:
    """Export training metrics to various formats"""
    
    @staticmethod
    def export_json(metrics: Dict, filepath: str):
        """Export metrics to JSON"""
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Metrics exported to {filepath}")
    
    @staticmethod
    def export_csv(metrics_history: List[Dict], filepath: str):
        """Export metrics history to CSV"""
        import csv
        
        if not metrics_history:
            return
        
        keys = metrics_history[0].keys()
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(metrics_history)
        
        print(f"✅ Metrics exported to {filepath}")


if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    
    monitor = RealtimeMetricsDisplay(root)
    
    # Simulate data
    import time
    for i in range(50):
        reward = 40 + np.random.normal(0, 5) + i * 0.5
        loss = 0.4 - i * 0.003 + np.random.normal(0, 0.02)
        unc = 0.6 - i * 0.003 + np.random.normal(0, 0.02)
        actions = [
            np.random.randint(0, 20),
            np.random.randint(20, 40),
            np.random.randint(10, 30)
        ]
        
        monitor.add_episode_data(reward, loss, unc, actions)
        monitor.update()
        time.sleep(0.05)
    
    root.deiconify()
    root.mainloop()
