#!/usr/bin/env python3
"""
Complete DQN Training Script for Keyframe Selection
Trains agent on simulated SLAM environment with realistic rewards
"""

import numpy as np
import argparse
from dqn_agent import DQNAgent
from energy_battery_model import EnergyModel, BatteryMonitor, EnergyAwareRewardCalculator
from degradation_policy import SLAMDegradationPolicy
from monitoring_logging import TrainingLogger, SLAMMetricsTracker
import time


class SLAMSimulator:
    """
    Simulated SLAM environment for training DQN
    Provides realistic state transitions and rewards
    """
    
    def __init__(self, episode_length: int = 200, battery_profile: str = 'constant'):
        """
        Initialize SLAM simulator
        
        Args:
            episode_length: Steps per episode
            battery_profile: 'constant', 'declining', or 'variable'
        """
        self.episode_length = episode_length
        self.battery_profile = battery_profile
        
        self.reset()
    
    def reset(self):
        """Reset environment for new episode"""
        self.step_count = 0
        self.uncertainty = np.random.uniform(0.3, 0.7)
        self.tracking_quality = 1.0
        self.feature_count = 500
        self.accumulated_translation = 0.0
        self.accumulated_rotation = 0.0
        
        if self.battery_profile == 'declining':
            self.battery = 100.0
        elif self.battery_profile == 'variable':
            self.battery = np.random.uniform(30, 100)
        else:  # constant
            self.battery = 80.0
        
        self.prev_uncertainty = self.uncertainty
        self.keyframes_stored = 0
    
    def step(self, action: int) -> tuple:
        """
        Execute one step in simulation
        
        Args:
            action: 0=skip, 1=save_normal, 2=save_light
            
        Returns:
            (next_state, reward, done, info)
        """
        self.step_count += 1
        
        # Simulate uncertainty dynamics
        if action == 0:  # SKIP
            # Skipping increases uncertainty slightly
            uncertainty_delta = np.random.uniform(0.02, 0.05)
            self.uncertainty = min(1.0, self.uncertainty + uncertainty_delta)
            
            # Feature count decreases without keyframe
            self.feature_count = max(50, self.feature_count - np.random.randint(10, 50))
            
        else:  # SAVE (normal or light)
            # Saving reduces uncertainty
            uncertainty_delta = np.random.uniform(0.05, 0.15)
            self.uncertainty = max(0.0, self.uncertainty - uncertainty_delta)
            
            # Feature count increases with keyframe
            self.feature_count = min(2000, self.feature_count + np.random.randint(50, 150))
            
            self.keyframes_stored += 1
        
        # Stochastic motion
        self.accumulated_translation += np.random.uniform(0.1, 0.3)
        self.accumulated_rotation += np.random.uniform(2, 5)
        
        # Tracking can fail with low features
        if self.feature_count < 50:
            self.tracking_quality = np.random.uniform(0.3, 0.7)
        elif self.feature_count < 100:
            self.tracking_quality = np.random.uniform(0.6, 0.9)
        else:
            self.tracking_quality = np.random.uniform(0.85, 1.0)
        
        # Occasional tracking loss
        if np.random.random() < 0.05:
            self.tracking_quality = np.random.uniform(0.0, 0.3)
        
        # Battery drain
        if self.battery_profile == 'declining':
            self.battery = max(5, self.battery - np.random.uniform(0.1, 0.3))
        elif self.battery_profile == 'variable':
            self.battery = max(5, self.battery - np.random.uniform(0.05, 0.15))
        
        # Build next state
        next_state = self._build_state()
        
        # Determine if tracking is OK
        tracking_ok = self.tracking_quality > 0.5
        
        # Done flag
        done = (self.step_count >= self.episode_length)
        
        # Info
        info = {
            'step': self.step_count,
            'keyframes': self.keyframes_stored,
            'tracking_ok': tracking_ok,
            'battery': self.battery
        }
        
        return next_state, tracking_ok, done, info
    
    def _build_state(self) -> np.ndarray:
        """Build 7-element state vector"""
        # Normalize values
        uncertainty_norm = min(self.uncertainty, 1.0)
        feature_norm = min(self.feature_count / 2000.0, 1.0)
        translation_norm = min(self.accumulated_translation / 10.0, 1.0)
        rotation_norm = min(self.accumulated_rotation / 360.0, 1.0)
        battery_norm = self.battery / 100.0
        
        delta_uncertainty = self.prev_uncertainty - self.uncertainty
        delta_uncertainty = np.clip(delta_uncertainty, -1.0, 1.0)
        
        time_since_kf = min(self.step_count - 10, 1.0) if self.keyframes_stored > 0 else 1.0
        
        state = np.array([
            uncertainty_norm,
            delta_uncertainty,
            feature_norm,
            translation_norm,
            rotation_norm,
            battery_norm,
            time_since_kf
        ], dtype=np.float32)
        
        self.prev_uncertainty = self.uncertainty
        return state
    
    def get_state(self) -> np.ndarray:
        """Get current state without stepping"""
        return self._build_state()


def train_dqn_agent(episodes: int = 500, episode_length: int = 200,
                    learning_rate: float = 1e-4, gamma: float = 0.99,
                    batch_size: int = 64, battery_profile: str = 'declining',
                    save_model_path: str = 'dqn_keyframe_model.pth',
                    device: str = 'cpu'):
    """
    Complete DQN training pipeline
    
    Args:
        episodes: Number of training episodes
        episode_length: Steps per episode
        learning_rate: DQN learning rate
        gamma: Discount factor
        batch_size: Training batch size
        battery_profile: 'constant', 'declining', or 'variable'
        save_model_path: Path to save trained model
        device: 'cpu' or 'cuda'
    """
    
    print("=" * 100)
    print(" " * 20 + "DQN TRAINING FOR INTELLIGENT KEYFRAME SELECTION")
    print("=" * 100)
    
    print(f"\nConfiguration:")
    print(f"  Episodes: {episodes}")
    print(f"  Episode Length: {episode_length}")
    print(f"  Learning Rate: {learning_rate}")
    print(f"  Gamma: {gamma}")
    print(f"  Batch Size: {batch_size}")
    print(f"  Battery Profile: {battery_profile}")
    print(f"  Device: {device}\n")
    
    # Initialize components
    agent = DQNAgent(
        state_dim=7, action_dim=3,
        learning_rate=learning_rate, gamma=gamma,
        epsilon_start=0.3, epsilon_end=0.05,
        epsilon_decay_steps=episodes * episode_length,
        device=device
    )
    
    energy_model = EnergyModel()
    battery_monitor = BatteryMonitor()
    reward_calculator = EnergyAwareRewardCalculator(energy_model, battery_monitor)
    
    simulator = SLAMSimulator(episode_length=episode_length, battery_profile=battery_profile)
    
    logger = TrainingLogger(log_dir="logs")
    metrics_tracker = SLAMMetricsTracker()
    
    # Training loop
    print(f"{'Episode':<10} {'Reward':<12} {'Avg Loss':<12} {'Epsilon':<10} {'Buffer Size':<12} {'Keyframes':<10}")
    print("-" * 100)
    
    for episode in range(episodes):
        state = simulator.reset()
        episode_reward = 0.0
        episode_loss = 0.0
        episode_steps = 0
        
        for step in range(episode_length):
            # Agent selects action
            action = agent.select_action(state, training=True)
            
            # Simulator executes action
            next_state, tracking_ok, done, info = simulator.step(action)
            
            # Calculate reward
            reward = reward_calculator.compute_reward(
                action=action,
                prev_uncertainty=simulator.prev_uncertainty,
                curr_uncertainty=simulator.uncertainty,
                tracking_ok=tracking_ok,
                keyframe_was_useful=(action > 0 and simulator.uncertainty < simulator.prev_uncertainty),
                battery_aware=True
            )
            
            # Store experience
            agent.store_experience(state, action, reward, next_state, done)
            
            # Train DQN
            loss = agent.train_step(batch_size=batch_size)
            
            # Update tracking
            episode_reward += reward
            if loss > 0:
                episode_loss += loss
                episode_steps += 1
            
            # Log metrics
            logger.log_step(
                episode=episode,
                step=step,
                action=action,
                reward=reward,
                uncertainty=simulator.uncertainty,
                battery=simulator.battery,
                loss=loss,
                epsilon=agent.epsilon,
                keyframes_created=simulator.keyframes_stored,
                tracking_ok=int(tracking_ok)
            )
            
            metrics_tracker.update(
                uncertainty=simulator.uncertainty,
                tracking_ok=tracking_ok,
                action=action,
                reward=reward,
                energy=energy_model.get_action_cost(action)
            )
            
            state = next_state
            
            if done:
                break
        
        # Episode complete
        avg_loss = episode_loss / max(1, episode_steps)
        agent.end_episode(episode_reward, episode_length)
        logger.log_episode(episode, episode_reward, episode_length, avg_loss,
                          simulator.keyframes_stored, 1.0)
        
        # Print progress
        if (episode + 1) % max(1, episodes // 20) == 0:
            summary = agent.get_summary()
            print(f"{episode + 1:<10} {episode_reward:<12.2f} {avg_loss:<12.4f} "
                  f"{agent.epsilon:<10.4f} {len(agent.replay_buffer):<12} {simulator.keyframes_stored:<10}")
    
    print("-" * 100)
    
    # Training complete
    print(f"\n✓ Training Complete!\n")
    
    summary = agent.get_summary()
    print(f"Final Statistics:")
    print(f"  Total Training Steps: {summary['training_steps']}")
    print(f"  Episodes Completed: {summary['episodes_completed']}")
    print(f"  Avg Reward (last 20): {summary['avg_reward_last_20']:.2f}")
    print(f"  Avg Length (last 20): {summary['avg_length_last_20']:.0f}")
    print(f"  Q-table Size: {summary['buffer_size']}")
    print(f"  Final Epsilon: {summary['epsilon']:.4f}\n")
    
    # Save model
    agent.save_model(save_model_path)
    logger.close()
    
    # Print metrics
    metrics_tracker.print_summary()
    
    print("=" * 100)
    print("Training finished! Model saved and logs written.\n")


def main():
    parser = argparse.ArgumentParser(description='Train DQN Agent for Keyframe Selection')
    parser.add_argument('--episodes', type=int, default=500,
                       help='Number of training episodes')
    parser.add_argument('--episode-length', type=int, default=200,
                       help='Steps per episode')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--gamma', type=float, default=0.99,
                       help='Discount factor')
    parser.add_argument('--batch-size', type=int, default=64,
                       help='Training batch size')
    parser.add_argument('--battery-profile', choices=['constant', 'declining', 'variable'],
                       default='declining', help='Battery profile for training')
    parser.add_argument('--model', default='dqn_keyframe_model.pth',
                       help='Path to save model')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu',
                       help='Device to train on')
    
    args = parser.parse_args()
    
    train_dqn_agent(
        episodes=args.episodes,
        episode_length=args.episode_length,
        learning_rate=args.lr,
        gamma=args.gamma,
        batch_size=args.batch_size,
        battery_profile=args.battery_profile,
        save_model_path=args.model,
        device=args.device
    )


if __name__ == "__main__":
    main()
