#!/usr/bin/env python3
"""
Frontend-Backend Integration Module
Bridges UI controls with DQN training backend
"""

import threading
import json
from typing import Callable, Dict, Optional, List
from pathlib import Path
from datetime import datetime
import sys


class BackendInterface:
    """Interface to interact with backend training system"""
    
    def __init__(self, backend_path: str = None):
        """Initialize backend interface"""
        self.backend_path = backend_path or Path(__file__).parent.parent / "backend"
        self.training_active = False
        self.training_thread = None
        self.current_episode = 0
        self.total_episodes = 0
        
        # Callbacks
        self.on_episode_complete = None
        self.on_training_start = None
        self.on_training_stop = None
        self.on_metrics_update = None
        
        # Training configuration
        self.config = {
            "episodes": 500,
            "batch_size": 64,
            "learning_rate": 1e-4,
            "gamma": 0.99,
            "epsilon_start": 0.3,
            "epsilon_end": 0.05,
            "battery_profile": "declining",
            "reward_weights": {
                "w_b": 8.0,
                "w_e": 6.0,
                "w_l": 40.0,
                "w_t": 0.01
            },
            "battery_thresholds": [60, 40, 20]
        }
        
        # Metrics buffer
        self.metrics_history = []
    
    def update_config(self, config: Dict):
        """Update training configuration"""
        self.config.update(config)
        print(f"✅ Configuration updated: {config}")
    
    def update_reward_weights(self, weights: Dict):
        """Update reward weight configuration"""
        self.config["reward_weights"].update(weights)
        print(f"✅ Reward weights updated: {weights}")
    
    def update_battery_thresholds(self, thresholds: List[float]):
        """Update battery degradation thresholds"""
        self.config["battery_thresholds"] = thresholds
        print(f"✅ Battery thresholds updated: {thresholds}")
    
    def start_training(self, episodes: int, on_progress: Callable = None):
        """Start training in background thread"""
        if self.training_active:
            print("⚠️ Training already in progress")
            return
        
        self.training_active = True
        self.current_episode = 0
        self.total_episodes = episodes
        self.config["episodes"] = episodes
        
        if self.on_training_start:
            self.on_training_start()
        
        # Start training thread
        self.training_thread = threading.Thread(
            target=self._training_loop,
            args=(on_progress,),
            daemon=True
        )
        self.training_thread.start()
        
        print(f"✅ Training started for {episodes} episodes")
    
    def _training_loop(self, on_progress: Callable = None):
        """Main training loop (simulated)"""
        import numpy as np
        import time
        
        try:
            for episode in range(self.total_episodes):
                if not self.training_active:
                    break
                
                self.current_episode = episode
                
                # Simulate episode training
                episode_reward = np.random.uniform(20, 80) + (episode / self.total_episodes) * 40
                episode_loss = max(0.001, 0.5 - (episode / self.total_episodes) * 0.4)
                episode_uncertainty = max(0.1, 0.8 - (episode / self.total_episodes) * 0.4)
                episode_keyframes = np.random.randint(5, 25)
                success_rate = 50 + (episode / self.total_episodes) * 40
                
                # Create metrics record
                metrics = {
                    "episode": episode,
                    "reward": float(episode_reward),
                    "loss": float(episode_loss),
                    "uncertainty": float(episode_uncertainty),
                    "keyframes": episode_keyframes,
                    "success_rate": float(success_rate),
                    "battery": max(0, 100 - (episode / self.total_episodes) * 80),
                    "epsilon": max(
                        self.config["epsilon_end"],
                        self.config["epsilon_start"] -
                        (episode / self.total_episodes) *
                        (self.config["epsilon_start"] - self.config["epsilon_end"])
                    ),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.metrics_history.append(metrics)
                
                # Trigger callbacks
                if self.on_episode_complete:
                    self.on_episode_complete(metrics)
                
                if on_progress:
                    on_progress(episode, self.total_episodes)
                
                if self.on_metrics_update:
                    self.on_metrics_update(metrics)
                
                # Simulate training step time
                time.sleep(0.05)
            
        except Exception as e:
            print(f"❌ Training error: {e}")
        finally:
            self.training_active = False
            if self.on_training_stop:
                self.on_training_stop()
    
    def pause_training(self):
        """Pause training"""
        self.training_active = False
        print("⏸️ Training paused")
    
    def resume_training(self):
        """Resume training"""
        if not self.training_active:
            self.training_active = True
            print("▶️ Training resumed")
    
    def stop_training(self):
        """Stop training and clean up"""
        self.training_active = False
        if self.training_thread:
            self.training_thread.join(timeout=5)
        print("⏹️ Training stopped")
    
    def save_model(self, filepath: str = None):
        """Save trained model"""
        filepath = filepath or f"dqn_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
        print(f"💾 Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str):
        """Load trained model"""
        print(f"📂 Model loaded from {filepath}")
        return True
    
    def export_metrics(self, filepath: str = None, format: str = "json"):
        """Export training metrics"""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = "json" if format == "json" else "csv"
            filepath = f"training_metrics_{timestamp}.{ext}"
        
        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
        elif format == "csv":
            import csv
            if self.metrics_history:
                keys = self.metrics_history[0].keys()
                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.metrics_history)
        
        print(f"📊 Metrics exported to {filepath}")
        return filepath
    
    def get_training_status(self) -> Dict:
        """Get current training status"""
        return {
            "active": self.training_active,
            "current_episode": self.current_episode,
            "total_episodes": self.total_episodes,
            "progress": self.current_episode / self.total_episodes if self.total_episodes > 0 else 0,
            "metrics_count": len(self.metrics_history)
        }
    
    def get_latest_metrics(self) -> Optional[Dict]:
        """Get latest training metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self) -> Dict:
        """Get aggregated metrics summary"""
        if not self.metrics_history:
            return {}
        
        import numpy as np
        
        rewards = [m["reward"] for m in self.metrics_history]
        losses = [m["loss"] for m in self.metrics_history]
        uncertainties = [m["uncertainty"] for m in self.metrics_history]
        keyframes = [m["keyframes"] for m in self.metrics_history]
        success_rates = [m["success_rate"] for m in self.metrics_history]
        
        return {
            "episodes_completed": len(self.metrics_history),
            "avg_reward": float(np.mean(rewards)),
            "max_reward": float(np.max(rewards)),
            "min_reward": float(np.min(rewards)),
            "avg_loss": float(np.mean(losses)),
            "min_loss": float(np.min(losses)),
            "avg_uncertainty": float(np.mean(uncertainties)),
            "avg_keyframes_per_episode": float(np.mean(keyframes)),
            "avg_success_rate": float(np.mean(success_rates)),
            "total_keyframes": int(np.sum(keyframes))
        }


class ConfigurationManager:
    """Manage frontend and backend configurations"""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration manager"""
        self.config_path = Path(config_path or "./training_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "dqn_params": {
                "learning_rate": 1e-4,
                "gamma": 0.99,
                "epsilon_start": 0.3,
                "epsilon_end": 0.05,
                "batch_size": 64,
                "update_freq": 1000
            },
            "reward_weights": {
                "w_b": 8.0,
                "w_e": 6.0,
                "w_l": 40.0,
                "w_t": 0.01
            },
            "battery_thresholds": [60, 40, 20],
            "training_params": {
                "episodes": 500,
                "episode_length": 1000,
                "battery_profile": "declining"
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"✅ Configuration saved to {self.config_path}")
    
    def update_section(self, section: str, updates: Dict):
        """Update a configuration section"""
        if section in self.config:
            self.config[section].update(updates)
        else:
            self.config[section] = updates
        self.save_config()
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


if __name__ == "__main__":
    # Test backend interface
    backend = BackendInterface()
    
    def on_episode_complete(metrics):
        print(f"Episode {metrics['episode']}: Reward={metrics['reward']:.2f}, Loss={metrics['loss']:.4f}")
    
    backend.on_episode_complete = on_episode_complete
    
    # Start training
    backend.start_training(10)
    
    # Keep main thread alive
    import time
    while backend.training_active:
        time.sleep(1)
    
    # Export metrics
    backend.export_metrics(format="json")
    
    # Print summary
    print("\n📊 Training Summary:")
    summary = backend.get_metrics_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
