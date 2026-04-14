#!/usr/bin/env python3
"""
Integrated Complete Stereo SLAM System
Combines best features from main_enhanced.py and slam_main.py
- Real-time dual camera display with statistics
- Live 3D visualization with animation
- Advanced SLAM with loop closure
- Professional UI with multiple display modes
- Battery-aware dynamic keyframe management
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

from camera_stream_handler import StereoCameraManager
from stereo_slam import StereoSLAMSystem


class BatteryManager:
    """Monitor and manage battery state for adaptive SLAM processing"""
    
    # Battery thresholds for different modes
    BATTERY_CRITICAL = 5  # Below 5%: aggressive frame skipping
    BATTERY_LOW = 15      # Below 15%: moderate frame skipping
    BATTERY_NORMAL = 50   # Below 50%: light frame skipping
    BATTERY_GOOD = 100    # Above 50%: no frame skipping
    
    def __init__(self):
        """Initialize battery manager"""
        self.current_battery = 100.0
        self.last_update = time.time()
        self.update_interval = 5.0  # Update every 5 seconds
    
    def update_battery_state(self) -> float:
        """Update and return current battery percentage"""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            try:
                battery = psutil.sensors_battery()
                if battery is not None:
                    self.current_battery = battery.percent
                self.last_update = current_time
            except Exception as e:
                # If battery info unavailable, assume good battery
                pass
        return self.current_battery
    
    def get_mode(self) -> str:
        """Get current battery mode"""
        if self.current_battery < self.BATTERY_CRITICAL:
            return 'critical'
        elif self.current_battery < self.BATTERY_LOW:
            return 'low'
        elif self.current_battery < self.BATTERY_NORMAL:
            return 'moderate'
        else:
            return 'good'
    
    def should_skip_frame(self, frame_count: int) -> bool:
        """Determine if frame should be skipped based on battery state"""
        mode = self.get_mode()
        
        if mode == 'critical':
            # Skip 7 out of 8 frames (process every 8th frame)
            return frame_count % 8 != 0
        elif mode == 'low':
            # Skip 3 out of 4 frames (process every 4th frame)
            return frame_count % 4 != 0
        elif mode == 'moderate':
            # Skip 1 out of 2 frames (process every other frame)
            return frame_count % 2 != 0
        else:
            # Process all frames
            return False
    
    def get_keyframe_threshold_multiplier(self) -> float:
        """Get displacement threshold multiplier for keyframe creation"""
        mode = self.get_mode()
        
        if mode == 'critical':
            return 3.0  # Require 3x displacement for keyframe
        elif mode == 'low':
            return 2.0  # Require 2x displacement for keyframe
        elif mode == 'moderate':
            return 1.5  # Require 1.5x displacement for keyframe
        else:
            return 1.0  # Normal displacement threshold


class IntegratedSLAMVisualizer:
    """Advanced real-time visualization for Integrated Stereo SLAM"""
    
    def __init__(self, figure_size: tuple = (14, 10)):
        self.fig = None
        self.ax = None
        self.figure_size = figure_size
        self.running = False
        self.last_update = time.time()
        
    def initialize(self):
        """Initialize visualization"""
        self.fig = plt.figure(figsize=self.figure_size)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X (m)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
        self.ax.set_zlabel('Z (m)', fontsize=12, fontweight='bold')
        self.ax.set_title('Integrated Stereo SLAM - Real-Time 3D Map', 
                         fontsize=14, fontweight='bold')
    
    def render(self, slam_system: StereoSLAMSystem, stats: dict):
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
            max_pts = 8000  # Show more points for better visualization
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
        title = (f"Integrated Stereo SLAM | "
                f"Keyframes: {keyframes_info['total_keyframes']} | "
                f"Points: {keyframes_info['total_points']} | "
                f"Loops: {keyframes_info['loop_closures']} | "
                f"FPS: {stats.get('fps', 0):.1f}")
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


class IntegratedStereoSLAMSystem:
    """Complete integrated Stereo SLAM application"""
    
    def __init__(self, left_camera_url: str, right_camera_url: str):
        """Initialize integrated SLAM system"""
        self.left_camera_url = left_camera_url
        self.right_camera_url = right_camera_url
        
        self.camera_manager = StereoCameraManager(left_camera_url, right_camera_url)
        self.slam_system = StereoSLAMSystem(
            max_keyframes=100,
            min_displacement=0.05,
            loop_closure_threshold=0.75
        )
        self.visualizer = IntegratedSLAMVisualizer()
        self.battery_manager = BatteryManager()
        
        self.running = False
        self.processed_frames = 0
        self.skipped_frames = 0
        self.frame_rate = 0.0
        self.stats = {
            'fps': 0,
            'features_l': 0,
            'features_r': 0,
            'matches': 0,
            'is_keyframe': False,
            'battery': 100.0,
            'battery_mode': 'good',
            'skipped_frames': 0,
        }
    
    def run(self):
        """Run integrated SLAM system"""
        print("=" * 100)
        print(" " * 20 + "INTEGRATED COMPLETE STEREO SLAM SYSTEM")
        print(" " * 15 + "Advanced Stereo Vision with Loop Closure Detection")
        print(" " * 15 + "with Battery-Aware Dynamic Keyframe Management")
        print("=" * 100)
        
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
        
        # Main SLAM loop
        print("\n[3/5] Starting Integrated Stereo SLAM processing...")
        print("Controls: 'q' = quit, 's' = save map, 'r' = reset view\n")
        
        self.running = True
        frame_times = []
        last_bundle_frame = 0
        frame_without_features = 0
        frame_counter = 0
        
        try:
            while self.running:
                start_time = time.time()
                frame_counter += 1
                
                # Update battery state
                current_battery = self.battery_manager.update_battery_state()
                battery_mode = self.battery_manager.get_mode()
                self.stats['battery'] = current_battery
                self.stats['battery_mode'] = battery_mode
                
                # Check if frame should be skipped based on battery
                if self.battery_manager.should_skip_frame(frame_counter):
                    self.skipped_frames += 1
                    self.stats['skipped_frames'] = self.skipped_frames
                    time.sleep(0.01)
                    continue
                
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
                
                # Adjust keyframe threshold based on battery state
                threshold_multiplier = self.battery_manager.get_keyframe_threshold_multiplier()
                adaptive_min_displacement = 0.05 * threshold_multiplier
                self.slam_system.min_displacement = adaptive_min_displacement
                
                # Process with SLAM
                is_keyframe = self.slam_system.process_stereo_pair(
                    left_frame, right_frame, timestamp=time.time()
                )
                
                self.stats['is_keyframe'] = is_keyframe
                
                # Periodic bundle adjustment (less frequent when battery is low)
                bundle_adjustment_interval = 5 if battery_mode == 'good' else (10 if battery_mode == 'moderate' else 20)
                if self.slam_system.keyframe_count > last_bundle_frame + bundle_adjustment_interval:
                    self.slam_system.optimize_bundle(max_iterations=2)
                    last_bundle_frame = self.slam_system.keyframe_count
                
                # Create enhanced display
                display = self._create_enhanced_display(left_frame, right_frame, is_keyframe)
                cv2.namedWindow("Integrated Stereo SLAM", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Integrated Stereo SLAM", 1600, 650)
                cv2.imshow("Integrated Stereo SLAM", display)
                
                # Keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nShutting down...")
                    break
                elif key == ord('s'):
                    self.slam_system.save_map("integrated_stereo_slam_map.json")
                    print("✓ Map saved!")
                
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
    
    def _create_enhanced_display(self, left_frame: np.ndarray, right_frame: np.ndarray,
                                 is_keyframe: bool) -> np.ndarray:
        """Create enhanced display with dual cameras and detailed statistics"""
        h1, w1 = left_frame.shape[:2]
        h2, w2 = right_frame.shape[:2]
        
        # Resize to consistent size
        target_h = 550
        target_w = int(target_h * w1 / h1)
        
        left_resized = cv2.resize(left_frame, (target_w, target_h))
        right_resized = cv2.resize(right_frame, (target_w, target_h))
        
        # Create separator with gradient
        separator = np.ones((target_h, 40, 3), dtype=np.uint8) * 50
        cv2.line(separator, (20, 0), (20, target_h), (100, 100, 255), 2)
        
        # Combine cameras
        composite = np.hstack([left_resized, separator, right_resized])
        
        # Create info bar at top
        info_bar_h = 100
        info_bar = np.ones((info_bar_h, composite.shape[1], 3), dtype=np.uint8) * 20
        
        # Add horizontal line
        cv2.line(info_bar, (0, info_bar_h - 1), (composite.shape[1], info_bar_h - 1), 
                (100, 150, 255), 2)
        
        composite = np.vstack([info_bar, composite])
        
        # Add information
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_color = (0, 255, 100)
        
        # Title
        cv2.putText(composite, "INTEGRATED STEREO SLAM SYSTEM", (20, 30),
                   font, 1.3, font_color, 2)
        
        # Statistics
        slam_info = self.slam_system.get_keyframes_info()
        stats_text = [
            f"Frame: {slam_info['frames_processed']}",
            f"Keyframes: {slam_info['total_keyframes']}",
            f"Points: {slam_info['total_points']}",
        ]
        
        x_offset = 20
        y_offset = 65
        for text in stats_text:
            cv2.putText(composite, text, (x_offset, y_offset),
                       font, 0.9, (200, 200, 200), 1)
            x_offset += 280
        
        # Battery information
        battery = self.stats.get('battery', 100.0)
        battery_mode = self.stats.get('battery_mode', 'good')
        skipped = self.stats.get('skipped_frames', 0)
        
        # Battery color based on mode
        battery_color = {
            'critical': (0, 0, 255),    # Red
            'low': (0, 165, 255),       # Orange
            'moderate': (0, 255, 255),  # Yellow
            'good': (0, 255, 0)         # Green
        }.get(battery_mode, (0, 255, 0))
        
        battery_text = f"Battery: {battery:.1f}% [{battery_mode.upper()}]"
        cv2.putText(composite, battery_text, (composite.shape[1] - 550, 65),
                   font, 0.85, battery_color, 2)
        
        skipped_text = f"Skipped: {skipped}"
        cv2.putText(composite, skipped_text, (composite.shape[1] - 550, 85),
                   font, 0.85, (100, 200, 255), 1)
        
        # Status and FPS (right side)
        status_color = (0, 255, 0) if is_keyframe else (100, 150, 255)
        status_text = "🔑 KEYFRAME" if is_keyframe else "→ TRACKING"
        
        cv2.putText(composite, status_text, (composite.shape[1] - 380, 65),
                   font, 1.0, status_color, 2)
        
        if self.frame_rate > 0:
            fps_text = f"FPS: {self.frame_rate:.1f}"
            cv2.putText(composite, fps_text, (composite.shape[1] - 220, 65),
                       font, 0.95, (0, 255, 255), 2)
        
        # Loop closures
        loop_text = f"Loops: {slam_info['loop_closures']}"
        cv2.putText(composite, loop_text, (composite.shape[1] - 380, 85),
                   font, 0.85, (100, 200, 255), 1)
        
        # Camera labels
        cv2.putText(composite, "LEFT CAMERA", (30, target_h + info_bar_h - 15),
                   font, 0.8, (255, 200, 100), 1)
        cv2.putText(composite, "RIGHT CAMERA", (target_w + 80, target_h + info_bar_h - 15),
                   font, 0.8, (255, 200, 100), 1)
        
        return composite
    
    def _visualization_loop(self):
        """Run 3D visualization in background thread"""
        try:
            self.visualizer.initialize()
            
            def update_plot(frame):
                self.visualizer.render(self.slam_system, self.stats)
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
        print("\n" + "=" * 100)
        print(" " * 35 + "FINAL SLAM STATISTICS")
        print("=" * 100)
        
        slam_info = self.slam_system.get_keyframes_info()
        print(f"\n📊 Processing Summary:")
        print(f"   • Total frames processed: {slam_info['frames_processed']}")
        print(f"   • Keyframes created: {slam_info['total_keyframes']}")
        print(f"   • Frames skipped (battery): {self.skipped_frames}")
        
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
        
        print(f"\n🔋 Battery-Aware Statistics:")
        print(f"   • Final battery level: {self.stats.get('battery', 100.0):.1f}%")
        print(f"   • Battery mode: {self.stats.get('battery_mode', 'good').upper()}")
        print(f"   • Energy efficiency: {(self.skipped_frames / max(self.processed_frames + self.skipped_frames, 1) * 100):.1f}% frame reduction")
        
        # Save map
        print(f"\n💾 Saving integrated SLAM map...")
        self.slam_system.save_map("integrated_stereo_slam_map.json")
        
        print("\n" + "=" * 100)
        print("✓ Integrated SLAM system successfully shut down\n")


def main():
    parser = argparse.ArgumentParser(description='Integrated Complete Stereo SLAM System')
    parser.add_argument('--left-camera', default='http://192.168.1.47/stream',
                       help='Left camera URL')
    parser.add_argument('--right-camera', default='http://192.168.1.48/stream',
                       help='Right camera URL')
    args = parser.parse_args()
    
    print(f"\n📷 Camera Configuration:")
    print(f"   Left:  {args.left_camera}")
    print(f"   Right: {args.right_camera}\n")
    
    system = IntegratedStereoSLAMSystem(args.left_camera, args.right_camera)
    system.run()


if __name__ == "__main__":
    main()
