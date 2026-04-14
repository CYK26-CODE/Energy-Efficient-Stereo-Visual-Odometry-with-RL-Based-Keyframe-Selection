#!/usr/bin/env python3
"""
Ultimate Integrated Stereo SLAM System with RL-Based Intelligent Keyframe Selection
Combines ALL best features:
- 2D trajectory overlay on left camera
- Real-time dual camera display
- Live 3D visualization with animation
- Advanced SLAM with loop closure
- Professional UI with rich statistics
- Mini trajectory visualization
- Feature matching visualization
- RL-Based Intelligent Keyframe Selection
"""

import cv2
import numpy as np
import time
import argparse
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
import psutil
import os
import json

from camera_stream_handler import StereoCameraManager
from stereo_slam import StereoSLAMSystem
from rl_keyframe_selector import RLKeyframeSelector, KeyframeAction, LocalizationUncertaintyMetrics, EnergyModel


class UltimateIntegratedSLAMVisualizer:
    """Advanced real-time visualization for Ultimate Stereo SLAM"""
    
    def __init__(self, figure_size: tuple = (14, 10)):
        self.fig = None
        self.ax = None
        self.figure_size = figure_size
        self.running = False
        
    def initialize(self):
        """Initialize visualization"""
        self.fig = plt.figure(figsize=self.figure_size)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X (m)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
        self.ax.set_zlabel('Z (m)', fontsize=12, fontweight='bold')
        self.ax.set_title('Ultimate Stereo SLAM + RL - Real-Time 3D Map', 
                         fontsize=14, fontweight='bold')
    
    def render(self, slam_system: StereoSLAMSystem, stats: dict, rl_stats: dict = None):
        """Render SLAM visualization with enhanced styling"""
        if self.ax is None:
            self.initialize()
        
        self.ax.clear()
        
        # Get data
        points, colors = slam_system.get_point_cloud()
        trajectory = slam_system.get_trajectory()
        keyframes_info = slam_system.get_keyframes_info()
        
        # Plot point cloud with better coloring
        if len(points) > 0:
            max_pts = 10000
            if len(points) > max_pts:
                indices = np.linspace(0, len(points) - 1, max_pts, dtype=int)
                disp_points = points[indices]
                disp_colors = colors[indices]
            else:
                disp_points = points
                disp_colors = colors
            
            norm_colors = np.clip(disp_colors.astype(float) / 255.0, 0, 1)
            self.ax.scatter(disp_points[:, 0], disp_points[:, 1], disp_points[:, 2],
                          c=norm_colors, s=3, alpha=0.6, depthshade=False)
        
        # Plot trajectory with enhanced styling
        if len(trajectory) > 1:
            self.ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                        'r-', linewidth=4, label='Camera Path', alpha=0.8)
            
            # Start marker (green circle)
            self.ax.scatter(*trajectory[0], color='lime', s=400, marker='o',
                          label='Start', zorder=10, edgecolors='darkgreen', linewidths=3)
            
            # End marker (red square)
            self.ax.scatter(*trajectory[-1], color='red', s=400, marker='s',
                          label='Current', zorder=10, edgecolors='darkred', linewidths=3)
            
            # Direction arrow
            if len(trajectory) > 1:
                mid_idx = len(trajectory) // 2
                direction = trajectory[-1] - trajectory[mid_idx]
                norm_dir = direction / (np.linalg.norm(direction) + 1e-6)
                arrow_length = 0.3
                arrow_start = trajectory[-1]
                arrow_end = arrow_start + norm_dir * arrow_length
                self.ax.plot([arrow_start[0], arrow_end[0]],
                           [arrow_start[1], arrow_end[1]],
                           [arrow_start[2], arrow_end[2]],
                           'r-', linewidth=3, alpha=0.9)
        
        # Enhanced title with rich statistics
        rl_info = ""
        if rl_stats:
            rl_info = f" | RL: {rl_stats.get('rl_action', 'N/A')} | Uncertainty: {rl_stats.get('uncertainty', 0):.2f}"
        
        title = (f"Ultimate Stereo SLAM + RL | "
                f"Keyframes: {keyframes_info['total_keyframes']} | "
                f"Points: {keyframes_info['total_points']} | "
                f"Loops: {keyframes_info['loop_closures']} | "
                f"FPS: {stats.get('fps', 0):.1f}{rl_info}")
        self.ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        
        # Auto scale with margin
        if len(points) > 0 or len(trajectory) > 0:
            all_pts = np.vstack([points if len(points) > 0 else np.zeros((1, 3)),
                                trajectory if len(trajectory) > 0 else np.zeros((1, 3))])
            margin = 1.0
            self.ax.set_xlim([all_pts[:, 0].min() - margin, all_pts[:, 0].max() + margin])
            self.ax.set_ylim([all_pts[:, 1].min() - margin, all_pts[:, 1].max() + margin])
            self.ax.set_zlim([all_pts[:, 2].min() - margin, all_pts[:, 2].max() + margin])
        
        # Legend
        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            self.ax.legend(handles, labels, loc='upper left', fontsize=10, 
                         framealpha=0.95, edgecolor='black')
        
        self.ax.view_init(elev=25, azim=45)
        self.ax.grid(True, alpha=0.3, linestyle='--')


class BatteryManager:
    """Monitor and manage battery state for adaptive SLAM processing"""
    
    BATTERY_CRITICAL = 5
    BATTERY_LOW = 15
    BATTERY_NORMAL = 50
    BATTERY_GOOD = 100
    
    def __init__(self):
        """Initialize battery manager"""
        self.current_battery = 100.0
        self.last_update = time.time()
        self.update_interval = 5.0
    
    def update_battery_state(self) -> float:
        """Update and return current battery percentage"""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            try:
                battery = psutil.sensors_battery()
                if battery is not None:
                    self.current_battery = battery.percent
                self.last_update = current_time
            except:
                pass
        return self.current_battery
    
    def get_battery_mode(self) -> str:
        """Get battery mode based on current percentage"""
        if self.current_battery < self.BATTERY_CRITICAL:
            return 'critical'
        elif self.current_battery < self.BATTERY_LOW:
            return 'low'
        elif self.current_battery < self.BATTERY_NORMAL:
            return 'moderate'
        else:
            return 'good'


class UltimateIntegratedStereoSLAMWithRL:
    """Ultimate integrated Stereo SLAM application with RL agent"""
    
    def __init__(self, left_camera_url: str, right_camera_url: str, 
                 use_rl: bool = True, rl_model_path: str = None, training_mode: bool = False):
        """Initialize ultimate SLAM system with RL"""
        self.left_camera_url = left_camera_url
        self.right_camera_url = right_camera_url
        
        self.camera_manager = StereoCameraManager(left_camera_url, right_camera_url)
        self.slam_system = StereoSLAMSystem(
            max_keyframes=100,
            min_displacement=0.05,
            loop_closure_threshold=0.75
        )
        self.visualizer = UltimateIntegratedSLAMVisualizer()
        
        # Battery management
        self.battery_manager = BatteryManager()
        
        # RL Agent setup
        self.use_rl = use_rl
        self.training_mode = training_mode
        self.rl_agent = None
        self.rl_model_path = rl_model_path or "rl_keyframe_model.json"
        
        if self.use_rl:
            self.rl_agent = RLKeyframeSelector(learning_rate=0.1, discount_factor=0.95,
                                              epsilon=0.05 if not training_mode else 0.2)
            if os.path.exists(self.rl_model_path) and not training_mode:
                self.rl_agent.load_model(self.rl_model_path)
        
        self.running = False
        self.processed_frames = 0
        self.frame_rate = 0.0
        self.stats = {
            'fps': 0,
            'features_l': 0,
            'features_r': 0,
            'matches': 0,
            'is_keyframe': False,
        }
        
        self.rl_stats = {
            'rl_action': 'N/A',
            'uncertainty': 0.5,
            'energy_need': 0.5,
            'battery_mode': 'good',
        }
        
        self.prev_uncertainty = 0.5
    
    def run(self):
        """Run ultimate SLAM system with RL"""
        mode_str = "TRAINING" if self.training_mode else "INFERENCE"
        print("=" * 110)
        print(" " * 15 + "ULTIMATE INTEGRATED STEREO SLAM + RL-BASED KEYFRAME SELECTION")
        print(" " * 20 + f"({mode_str} MODE)" if self.use_rl else "")
        print(" " * 10 + "Advanced Stereo Vision with Loop Closure + Intelligent Keyframe Selection")
        print("=" * 110)
        
        # Start cameras
        print("\n[1/5] Connecting to stereo cameras...")
        max_retries = 5
        for attempt in range(max_retries):
            if self.camera_manager.start():
                print("✓ Cameras connected")
                break
            else:
                print(f"  Attempt {attempt + 1}/{max_retries}: Waiting for cameras...")
                time.sleep(2)
        else:
            print("ERROR: Could not connect to cameras after retries")
            return False
        
        # Start visualization thread
        print("\n[2/5] Starting real-time 3D visualization...")
        viz_thread = threading.Thread(target=self._visualization_loop, daemon=True)
        viz_thread.start()
        print("✓ Visualization thread started")
        
        # RL Agent info
        if self.use_rl:
            print("\n[2.5/5] RL Agent Active")
            print(f"✓ Mode: {mode_str}")
            print(f"✓ Model: {self.rl_model_path}")
        
        # Main SLAM loop
        print("\n[3/5] Starting Ultimate Stereo SLAM processing...")
        print("Controls: 'q' = quit, 's' = save map, 'r' = save RL model (if training)\n")
        
        self.running = True
        frame_times = []
        last_bundle_frame = 0
        frame_without_features = 0
        
        prev_uncertainty = 0.5
        prev_energy_need = 0.5
        
        try:
            while self.running:
                start_time = time.time()
                
                # Get stereo pair
                stereo_pair = self.camera_manager.get_stereo_pair()
                if stereo_pair is None:
                    time.sleep(0.01)
                    frame_without_features += 1
                    if frame_without_features % 100 == 0:
                        print("  Still waiting for valid frames...")
                    continue
                
                frame_without_features = 0
                left_frame, right_frame = stereo_pair
                self.processed_frames += 1
                
                # Update battery state
                current_battery = self.battery_manager.update_battery_state()
                battery_mode = self.battery_manager.get_battery_mode()
                self.rl_stats['battery_mode'] = battery_mode
                
                # RL Decision Making
                should_create_keyframe = True
                
                if self.use_rl and self.rl_agent is not None:
                    # Estimate localization uncertainty
                    uncertainty = self.rl_agent.uncertainty_metrics.update_from_slam(self.slam_system)
                    
                    # Estimate energy need from battery mode
                    energy_model = EnergyModel()
                    energy_need = energy_model.estimate_energy_reduction(battery_mode)
                    
                    self.rl_stats['uncertainty'] = uncertainty
                    self.rl_stats['energy_need'] = energy_need
                    
                    # Get RL decision
                    rl_action = self.rl_agent.select_action(
                        uncertainty, energy_need, battery_mode, training=self.training_mode
                    )
                    
                    should_create_keyframe = (rl_action == KeyframeAction.CREATE_KEYFRAME)
                    self.rl_stats['rl_action'] = "CREATE_KF" if should_create_keyframe else "SKIP_FRAME"
                    
                    # Learning in training mode
                    if self.training_mode:
                        next_uncertainty = uncertainty + np.random.normal(0, 0.05)
                        next_uncertainty = np.clip(next_uncertainty, 0, 1)
                        
                        self.rl_agent.learn_from_experience(
                            uncertainty, energy_need, battery_mode,
                            prev_uncertainty, should_create_keyframe,
                            next_uncertainty, energy_need, done=False
                        )
                    
                    prev_uncertainty = uncertainty
                    prev_energy_need = energy_need
                
                # Process with SLAM (conditional on RL decision)
                if should_create_keyframe:
                    is_keyframe = self.slam_system.process_stereo_pair(
                        left_frame, right_frame, timestamp=time.time()
                    )
                else:
                    # Skip SLAM processing - just update tracking visually
                    is_keyframe = False
                
                self.stats['is_keyframe'] = is_keyframe
                
                # Periodic bundle adjustment
                if self.slam_system.keyframe_count > last_bundle_frame + 5:
                    self.slam_system.optimize_bundle(max_iterations=2)
                    last_bundle_frame = self.slam_system.keyframe_count
                
                # Create ultimate display with all features
                display = self._create_ultimate_display(left_frame, right_frame, is_keyframe,
                                                       current_battery, battery_mode)
                cv2.namedWindow("Ultimate Stereo SLAM + RL - All Features", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Ultimate Stereo SLAM + RL - All Features", 1900, 750)
                cv2.imshow("Ultimate Stereo SLAM + RL - All Features", display)
                
                # Keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nShutting down...")
                    break
                elif key == ord('s'):
                    self.slam_system.save_map("ultimate_stereo_slam_rl_map.json")
                    print("✓ SLAM Map saved!")
                elif key == ord('r') and self.training_mode and self.use_rl:
                    self.rl_agent.save_model(self.rl_model_path)
                    print("✓ RL Model saved!")
                
                # FPS calculation
                frame_time = time.time() - start_time
                frame_times.append(frame_time)
                if len(frame_times) > 30:
                    frame_times.pop(0)
                    self.frame_rate = 1.0 / (sum(frame_times) / len(frame_times))
                    self.stats['fps'] = self.frame_rate
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"\nError: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
        
        return True
    
    def _create_ultimate_display(self, left_frame: np.ndarray, right_frame: np.ndarray,
                                is_keyframe: bool, battery_level: float, battery_mode: str) -> np.ndarray:
        """Create ultimate display with all features + RL info"""
        
        h1, w1 = left_frame.shape[:2]
        h2, w2 = right_frame.shape[:2]
        
        # Resize to consistent size
        target_h = 600
        target_w = int(target_h * w1 / h1)
        
        left_resized = cv2.resize(left_frame.copy(), (target_w, target_h))
        right_resized = cv2.resize(right_frame, (target_w, target_h))
        
        # ===== 2D TRAJECTORY OVERLAY =====
        trajectory = self.slam_system.get_trajectory()
        if len(trajectory) > 1:
            traj_2d = trajectory[:, :2]
            
            if len(traj_2d) > 0:
                min_x, min_y = traj_2d.min(axis=0)
                max_x, max_y = traj_2d.max(axis=0)
                
                overlay_size = 150
                margin = 10
                
                if (max_x - min_x) > 1e-6 and (max_y - min_y) > 1e-6:
                    scale = (overlay_size - 2*margin) / max(max_x - min_x, max_y - min_y)
                    traj_scaled = (traj_2d - [min_x, min_y]) * scale + margin
                    
                    overlay = np.zeros((overlay_size + 2*margin, overlay_size + 2*margin, 3), 
                                      dtype=np.uint8)
                    overlay[:] = [30, 30, 30]
                    
                    # Draw grid
                    for i in range(0, overlay_size + 2*margin, 30):
                        cv2.line(overlay, (i, 0), (i, overlay_size + 2*margin), (60, 60, 60), 1)
                        cv2.line(overlay, (0, i), (overlay_size + 2*margin, i), (60, 60, 60), 1)
                    
                    # Draw trajectory
                    for i in range(len(traj_scaled) - 1):
                        pt1 = tuple(traj_scaled[i].astype(int))
                        pt2 = tuple(traj_scaled[i + 1].astype(int))
                        color = (int(255 * (i / len(traj_scaled))), 100, 
                                int(100 + 155 * (i / len(traj_scaled))))
                        cv2.line(overlay, pt1, pt2, color, 2)
                    
                    # Draw start point (green)
                    cv2.circle(overlay, tuple(traj_scaled[0].astype(int)), 5, (0, 255, 0), -1)
                    cv2.circle(overlay, tuple(traj_scaled[0].astype(int)), 5, (0, 200, 0), 2)
                    
                    # Draw end point (red)
                    cv2.circle(overlay, tuple(traj_scaled[-1].astype(int)), 5, (0, 0, 255), -1)
                    cv2.circle(overlay, tuple(traj_scaled[-1].astype(int)), 5, (0, 0, 200), 2)
                    
                    # Draw border
                    cv2.rectangle(overlay, (0, 0), 
                                (overlay_size + 2*margin - 1, overlay_size + 2*margin - 1),
                                (100, 150, 255), 2)
                    
                    # Add label
                    cv2.putText(overlay, "2D Trajectory", (margin + 5, margin + 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
                    
                    # Blend onto left frame
                    left_resized[0:overlay.shape[0], 0:overlay.shape[1]] = \
                        cv2.addWeighted(left_resized[0:overlay.shape[0], 0:overlay.shape[1]], 0.6,
                                      overlay, 0.4, 0)
        
        # ===== SEPARATOR =====
        separator = np.ones((target_h, 40, 3), dtype=np.uint8) * 50
        cv2.line(separator, (20, 0), (20, target_h), (100, 100, 255), 2)
        
        # ===== COMBINE CAMERAS =====
        composite = np.hstack([left_resized, separator, right_resized])
        
        # ===== CREATE INFO BAR =====
        info_bar_h = 120
        info_bar = np.ones((info_bar_h, composite.shape[1], 3), dtype=np.uint8) * 20
        cv2.line(info_bar, (0, info_bar_h - 1), (composite.shape[1], info_bar_h - 1), 
                (100, 150, 255), 2)
        
        composite = np.vstack([info_bar, composite])
        
        # ===== ADD TEXT INFORMATION =====
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_color = (0, 255, 100)
        
        # Title
        title_suffix = " + RL AGENT" if self.use_rl else ""
        cv2.putText(composite, f"ULTIMATE STEREO SLAM + RL - ALL FEATURES{title_suffix}", (20, 30),
                   font, 1.0, font_color, 2)
        
        # Statistics
        slam_info = self.slam_system.get_keyframes_info()
        
        stats_x = 20
        stats_y = 55
        cv2.putText(composite, f"Frame: {slam_info['frames_processed']}", (stats_x, stats_y),
                   font, 0.7, (200, 200, 200), 1)
        cv2.putText(composite, f"Keyframes: {slam_info['total_keyframes']}", 
                   (stats_x + 280, stats_y), font, 0.7, (200, 200, 200), 1)
        cv2.putText(composite, f"Points: {slam_info['total_points']}", 
                   (stats_x + 600, stats_y), font, 0.7, (200, 200, 200), 1)
        cv2.putText(composite, f"Loops: {slam_info['loop_closures']}", 
                   (stats_x + 850, stats_y), font, 0.7, (200, 200, 200), 1)
        
        # RL Info
        if self.use_rl:
            rl_y = 85
            rl_color = (100, 200, 255)
            cv2.putText(composite, f"RL Action: {self.rl_stats['rl_action']}", 
                       (stats_x, rl_y), font, 0.7, rl_color, 1)
            cv2.putText(composite, f"Uncertainty: {self.rl_stats['uncertainty']:.3f}", 
                       (stats_x + 280, rl_y), font, 0.7, rl_color, 1)
            cv2.putText(composite, f"Battery: {battery_level:.1f}% ({battery_mode})", 
                       (stats_x + 650, rl_y), font, 0.7, rl_color, 1)
            cv2.putText(composite, f"Energy Need: {self.rl_stats['energy_need']:.3f}", 
                       (stats_x + 1150, rl_y), font, 0.7, rl_color, 1)
        else:
            # Just show battery info
            cv2.putText(composite, f"Battery: {battery_level:.1f}% ({battery_mode})", 
                       (stats_x + 850, 55), font, 0.7, (200, 200, 200), 1)
        
        # Status
        status_color = (0, 255, 0) if is_keyframe else (100, 150, 255)
        status_text = "🔑 KEYFRAME" if is_keyframe else "→ TRACKING"
        cv2.putText(composite, status_text, (composite.shape[1] - 520, 60),
                   font, 1.0, status_color, 2)
        
        # FPS
        if self.frame_rate > 0:
            cv2.putText(composite, f"FPS: {self.frame_rate:.1f}", 
                       (composite.shape[1] - 220, 60), font, 0.95, (0, 255, 255), 2)
        
        # Mode indicator
        mode_text = f"[{('TRAINING' if self.training_mode else 'INFERENCE')}]" if self.use_rl else ""
        cv2.putText(composite, f"{mode_text}", (composite.shape[1] - 200, 85),
                   font, 0.6, (150, 150, 150), 1)
        
        # Mini stats at bottom
        bottom_text = "2D Map | Real-Time Processing | Loop Closure Active"
        if self.use_rl:
            bottom_text += " | RL Keyframe Selection Active"
        cv2.putText(composite, bottom_text, (20, composite.shape[0] - 10), 
                   font, 0.65, (150, 150, 150), 1)
        
        return composite
    
    def _visualization_loop(self):
        """Run 3D visualization in background thread"""
        try:
            self.visualizer.initialize()
            
            def update_plot(frame):
                self.visualizer.render(self.slam_system, self.stats, self.rl_stats)
                return []
            
            ani = FuncAnimation(self.visualizer.fig, update_plot, interval=300, 
                              blit=True, cache_frame_data=False)
            plt.tight_layout()
            plt.show(block=False)
            
            while self.running:
                try:
                    plt.pause(0.3)
                except:
                    break
        
        except Exception as e:
            print(f"Visualization error: {str(e)}")
        finally:
            try:
                plt.close('all')
            except:
                pass
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n[4/5] Cleaning up...")
        
        self.running = False
        self.camera_manager.stop()
        cv2.destroyAllWindows()
        
        try:
            plt.close('all')
        except:
            pass
        
        # Print final statistics
        print("\n" + "=" * 110)
        print(" " * 30 + "ULTIMATE SLAM + RL - FINAL STATISTICS")
        print("=" * 110)
        
        slam_info = self.slam_system.get_keyframes_info()
        print(f"\n📊 Processing Summary:")
        print(f"   • Total frames processed: {slam_info['frames_processed']}")
        print(f"   • Keyframes created: {slam_info['total_keyframes']}")
        
        trajectory = self.slam_system.get_trajectory()
        if len(trajectory) > 1:
            total_dist = sum(np.linalg.norm(trajectory[i+1] - trajectory[i])
                           for i in range(len(trajectory)-1))
            print(f"\n🗺️  Trajectory Summary:")
            print(f"   • Distance traveled: {total_dist:.4f} meters")
            print(f"   • Start position: ({trajectory[0][0]:.3f}, {trajectory[0][1]:.3f}, {trajectory[0][2]:.3f})")
            print(f"   • End position: ({trajectory[-1][0]:.3f}, {trajectory[-1][1]:.3f}, {trajectory[-1][2]:.3f})")
        
        print(f"\n🌐 3D Map Summary:")
        print(f"   • Total 3D points: {slam_info['total_points']}")
        print(f"   • Loop closures detected: {slam_info['loop_closures']}")
        
        # RL Statistics
        if self.use_rl and self.rl_agent:
            print(f"\n🤖 RL Agent Summary:")
            print(f"   • Model: {self.rl_model_path}")
            print(f"   • Mode: {'TRAINING' if self.training_mode else 'INFERENCE'}")
            policy = self.rl_agent.get_policy_summary()
            print(f"   • States Explored: {policy['states_explored']}")
            print(f"   • Training Steps: {policy['training_steps']}")
        
        print(f"\n✨ Features Active:")
        print(f"   • 2D Trajectory Overlay: ✓ (Top-left corner)")
        print(f"   • Dual Camera Display: ✓ (Side-by-side)")
        print(f"   • Real-Time 3D Visualization: ✓ (Animated)")
        print(f"   • Loop Closure Detection: ✓")
        print(f"   • Bundle Adjustment: ✓")
        if self.use_rl:
            print(f"   • RL-Based Keyframe Selection: ✓ ({('TRAINING' if self.training_mode else 'INFERENCE')})")
        
        # Save files
        print(f"\n💾 Saving maps and models...")
        self.slam_system.save_map("ultimate_stereo_slam_rl_map.json")
        
        if self.use_rl and self.training_mode and self.rl_agent:
            self.rl_agent.save_model(self.rl_model_path)
        
        print("\n" + "=" * 110)
        print("✓ Ultimate Integrated SLAM + RL System successfully shut down\n")


def main():
    parser = argparse.ArgumentParser(description='Ultimate Integrated Stereo SLAM + RL System')
    parser.add_argument('--left-camera', default='http://192.168.1.47/stream',
                       help='Left camera URL')
    parser.add_argument('--right-camera', default='http://192.168.1.48/stream',
                       help='Right camera URL')
    parser.add_argument('--no-rl', action='store_true', 
                       help='Disable RL agent (use basic battery mode)')
    parser.add_argument('--train', action='store_true',
                       help='Train RL agent (learning mode)')
    parser.add_argument('--model', default='rl_keyframe_model.json',
                       help='Path to RL model file')
    args = parser.parse_args()
    
    print(f"\n📷 Camera Configuration:")
    print(f"   Left:  {args.left_camera}")
    print(f"   Right: {args.right_camera}")
    print(f"   RL Agent: {'ENABLED' if not args.no_rl else 'DISABLED'}")
    if not args.no_rl:
        print(f"   RL Mode: {'TRAINING' if args.train else 'INFERENCE'}")
        print(f"   Model: {args.model}\n")
    else:
        print()
    
    system = UltimateIntegratedStereoSLAMWithRL(
        args.left_camera, args.right_camera,
        use_rl=not args.no_rl,
        rl_model_path=args.model,
        training_mode=args.train
    )
    system.run()


if __name__ == "__main__":
    main()
