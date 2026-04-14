#!/usr/bin/env python3
"""
Logging and Monitoring System
Tracks training metrics and SLAM performance
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import numpy as np


class TrainingLogger:
    """
    Logs DQN training metrics
    Writes to CSV for analysis
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize training logger
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"training_{timestamp}.csv")
        self.metrics_file = os.path.join(log_dir, f"metrics_{timestamp}.json")
        
        # Initialize CSV
        self.fieldnames = [
            'episode', 'step', 'action', 'reward', 'uncertainty', 'battery',
            'loss', 'epsilon', 'keyframes_created', 'tracking_ok'
        ]
        
        self.csv_writer = None
        self.csv_file = None
        self._init_csv()
        
        # Memory for metrics
        self.metrics = defaultdict(list)
    
    def _init_csv(self):
        """Initialize CSV file"""
        self.csv_file = open(self.log_file, 'w', newline='')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
        self.csv_writer.writeheader()
        self.csv_file.flush()
    
    def log_step(self, episode: int, step: int, action: int, reward: float,
                 uncertainty: float, battery: float, loss: float, epsilon: float,
                 keyframes_created: int, tracking_ok: bool):
        """Log a single training step"""
        row = {
            'episode': episode,
            'step': step,
            'action': action,
            'reward': reward,
            'uncertainty': uncertainty,
            'battery': battery,
            'loss': loss,
            'epsilon': epsilon,
            'keyframes_created': keyframes_created,
            'tracking_ok': int(tracking_ok)
        }
        
        self.csv_writer.writerow(row)
        self.csv_file.flush()
        
        # Store metrics
        self.metrics['rewards'].append(reward)
        self.metrics['uncertainties'].append(uncertainty)
        self.metrics['actions'].append(action)
    
    def log_episode(self, episode: int, episode_reward: float, episode_length: int,
                    avg_loss: float, keyframes: int, tracking_success_rate: float):
        """Log episode summary"""
        self.metrics['episode_rewards'].append(episode_reward)
        self.metrics['episode_lengths'].append(episode_length)
        self.metrics['avg_losses'].append(avg_loss)
        self.metrics['keyframes_per_episode'].append(keyframes)
        self.metrics['success_rates'].append(tracking_success_rate)
    
    def save_metrics(self):
        """Save metrics summary to JSON"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_steps': len(self.metrics.get('rewards', [])),
            'total_episodes': len(self.metrics.get('episode_rewards', [])),
            'avg_reward': float(np.mean(self.metrics.get('episode_rewards', [0]))),
            'avg_episode_length': float(np.mean(self.metrics.get('episode_lengths', [0]))),
            'total_keyframes': int(np.sum(self.metrics.get('keyframes_per_episode', [0]))),
            'avg_success_rate': float(np.mean(self.metrics.get('success_rates', [0]))),
            'metrics_log': self.log_file
        }
        
        with open(self.metrics_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def close(self):
        """Close log file"""
        if self.csv_file:
            self.csv_file.close()
        self.save_metrics()


class SLAMMetricsTracker:
    """
    Tracks SLAM performance metrics during operation
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize metrics tracker
        
        Args:
            window_size: Size of rolling window for averaging
        """
        self.window_size = window_size
        
        # Rolling windows
        self.uncertainty_window = []
        self.tracking_window = []
        self.action_window = []
        self.reward_window = []
        self.energy_window = []
        
        # Counters
        self.total_frames = 0
        self.keyframes_created = 0
        self.frames_skipped = 0
        self.tracking_losses = 0
        
        # History
        self.history = {
            'uncertainties': [],
            'keyframes': [],
            'energy_consumed': []
        }
    
    def update(self, uncertainty: float, tracking_ok: bool, action: int, 
               reward: float, energy: float):
        """
        Update metrics with new frame data
        
        Args:
            uncertainty: Localization uncertainty [0, 1]
            tracking_ok: Whether tracking is OK
            action: Action taken (0=skip, 1=save, 2=save-light)
            reward: Reward received
            energy: Energy consumed this frame
        """
        self.total_frames += 1
        
        # Update windows
        self.uncertainty_window.append(uncertainty)
        self.tracking_window.append(1.0 if tracking_ok else 0.0)
        self.action_window.append(action)
        self.reward_window.append(reward)
        self.energy_window.append(energy)
        
        # Trim to window size
        if len(self.uncertainty_window) > self.window_size:
            self.uncertainty_window.pop(0)
            self.tracking_window.pop(0)
            self.action_window.pop(0)
            self.reward_window.pop(0)
            self.energy_window.pop(0)
        
        # Update counters
        if action > 0:
            self.keyframes_created += 1
        else:
            self.frames_skipped += 1
        
        if not tracking_ok:
            self.tracking_losses += 1
        
        # Update history
        self.history['uncertainties'].append(uncertainty)
        self.history['keyframes'].append(self.keyframes_created)
        self.history['energy_consumed'].append(energy)
    
    def get_current_metrics(self) -> Dict:
        """Get current rolling window metrics"""
        if not self.uncertainty_window:
            return {}
        
        return {
            'avg_uncertainty': float(np.mean(self.uncertainty_window)),
            'std_uncertainty': float(np.std(self.uncertainty_window)),
            'tracking_success_rate': float(np.mean(self.tracking_window)) * 100,
            'avg_reward': float(np.mean(self.reward_window)),
            'skip_ratio': float(np.sum([1 for a in self.action_window if a == 0])) / len(self.action_window) if self.action_window else 0,
            'save_ratio': float(np.sum([1 for a in self.action_window if a > 0])) / len(self.action_window) if self.action_window else 0,
            'avg_energy_per_frame': float(np.mean(self.energy_window))
        }
    
    def get_episode_summary(self) -> Dict:
        """Get episode summary"""
        total_actions = self.keyframes_created + self.frames_skipped
        
        return {
            'total_frames': self.total_frames,
            'keyframes_created': self.keyframes_created,
            'frames_skipped': self.frames_skipped,
            'skip_rate': float(self.frames_skipped) / total_actions if total_actions > 0 else 0,
            'tracking_losses': self.tracking_losses,
            'tracking_loss_rate': float(self.tracking_losses) / self.total_frames if self.total_frames > 0 else 0,
            'avg_uncertainty': float(np.mean(self.history['uncertainties'])) if self.history['uncertainties'] else 0,
            'total_energy': float(np.sum(self.history['energy_consumed']))
        }
    
    def print_summary(self):
        """Print episode summary"""
        summary = self.get_episode_summary()
        current = self.get_current_metrics()
        
        print("\n" + "=" * 80)
        print("📊 SLAM METRICS SUMMARY")
        print("=" * 80)
        
        print(f"\nFrame Statistics:")
        print(f"  • Total Frames Processed: {summary['total_frames']}")
        print(f"  • Keyframes Created: {summary['keyframes_created']}")
        print(f"  • Frames Skipped: {summary['frames_skipped']}")
        print(f"  • Skip Rate: {summary['skip_rate']:.1%}")
        
        print(f"\nTracking Quality:")
        print(f"  • Tracking Losses: {summary['tracking_losses']}")
        print(f"  • Loss Rate: {summary['tracking_loss_rate']:.1%}")
        print(f"  • Current Success Rate: {current.get('tracking_success_rate', 0):.1f}%")
        
        print(f"\nLocalization Quality:")
        print(f"  • Avg Uncertainty: {summary['avg_uncertainty']:.4f}")
        print(f"  • Current Avg Uncertainty: {current.get('avg_uncertainty', 0):.4f}")
        
        print(f"\nEnergy Consumption:")
        print(f"  • Total Energy: {summary['total_energy']:.2f} units")
        print(f"  • Avg per Frame: {current.get('avg_energy_per_frame', 0):.4f}")
        
        print(f"\nAction Distribution:")
        print(f"  • Skip: {current.get('skip_ratio', 0):.1%}")
        print(f"  • Save: {current.get('save_ratio', 0):.1%}")
        
        print("=" * 80 + "\n")


class PerformanceEvaluator:
    """
    Evaluates Pareto front and policy performance
    """
    
    def __init__(self):
        """Initialize evaluator"""
        self.runs = []
    
    def add_run(self, run_id: str, battery_avg: float, energy_used: float,
                uncertainty_avg: float, tracking_success: float, keyframes: int):
        """
        Add a run to evaluation
        
        Args:
            run_id: Run identifier
            battery_avg: Average battery during run
            energy_used: Total energy consumed
            uncertainty_avg: Average localization uncertainty
            tracking_success: Tracking success rate [0, 1]
            keyframes: Number of keyframes created
        """
        self.runs.append({
            'run_id': run_id,
            'battery_avg': battery_avg,
            'energy_used': energy_used,
            'uncertainty_avg': uncertainty_avg,
            'tracking_success': tracking_success,
            'keyframes': keyframes
        })
    
    def get_pareto_front(self) -> List[Dict]:
        """
        Get Pareto front (non-dominated solutions)
        Objective: minimize energy & uncertainty, maximize tracking success
        
        Returns:
            List of Pareto-optimal runs
        """
        if not self.runs:
            return []
        
        pareto_front = []
        
        for candidate in self.runs:
            dominated = False
            
            for other in self.runs:
                if candidate == other:
                    continue
                
                # Check if other dominates candidate
                # (lower energy, lower uncertainty, higher success)
                if (other['energy_used'] <= candidate['energy_used'] and
                    other['uncertainty_avg'] <= candidate['uncertainty_avg'] and
                    other['tracking_success'] >= candidate['tracking_success']):
                    
                    if not (other['energy_used'] == candidate['energy_used'] and
                            other['uncertainty_avg'] == candidate['uncertainty_avg'] and
                            other['tracking_success'] == candidate['tracking_success']):
                        dominated = True
                        break
            
            if not dominated:
                pareto_front.append(candidate)
        
        return sorted(pareto_front, key=lambda x: x['energy_used'])
    
    def print_comparison(self):
        """Print comparison of all runs"""
        print("\n" + "=" * 100)
        print("📈 PERFORMANCE COMPARISON")
        print("=" * 100)
        
        print(f"\n{'Run ID':<15} {'Battery':<10} {'Energy':<12} {'Uncertainty':<15} {'Tracking':<12} {'Keyframes':<10}")
        print("-" * 100)
        
        for run in self.runs:
            print(f"{run['run_id']:<15} {run['battery_avg']:>6.1f}% {run['energy_used']:>10.2f} "
                  f"{run['uncertainty_avg']:>14.4f} {run['tracking_success']:>10.1%} {run['keyframes']:>10}")
        
        print("\n" + "Pareto Front (Non-dominated solutions):")
        print("-" * 100)
        
        pareto = self.get_pareto_front()
        for run in pareto:
            print(f"{run['run_id']:<15} {run['battery_avg']:>6.1f}% {run['energy_used']:>10.2f} "
                  f"{run['uncertainty_avg']:>14.4f} {run['tracking_success']:>10.1%} {run['keyframes']:>10}")
        
        print("=" * 100 + "\n")
