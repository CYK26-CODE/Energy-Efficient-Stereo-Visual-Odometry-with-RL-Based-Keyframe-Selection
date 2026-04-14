#!/usr/bin/env python3
"""
RL Agent Training Script for Intelligent Keyframe Selection
Trains the agent in simulation before deployment on actual SLAM system
"""

import numpy as np
import argparse
import json
from rl_keyframe_selector import RLKeyframeSelector, KeyframeAction, LocalizationUncertaintyMetrics, EnergyModel


class SLAMSimulator:
    """Simulate SLAM system for RL training"""
    
    def __init__(self, episode_length: int = 100):
        """Initialize SLAM simulator"""
        self.episode_length = episode_length
        self.step_count = 0
        self.uncertainty = 0.5
        self.energy_need = 0.5
        self.battery_mode = 'good'
        self.frames_skipped = 0
        
    def reset(self):
        """Reset environment for new episode"""
        self.step_count = 0
        self.uncertainty = np.random.uniform(0.2, 0.8)
        self.energy_need = np.random.uniform(0.1, 0.9)
        self.battery_mode = np.random.choice(['critical', 'low', 'moderate', 'good'])
        self.frames_skipped = 0
        return self.get_state()
    
    def get_state(self):
        """Get current state"""
        return {
            'uncertainty': self.uncertainty,
            'energy_need': self.energy_need,
            'battery_mode': self.battery_mode
        }
    
    def step(self, action: KeyframeAction):
        """
        Execute one step in the environment
        
        Returns:
            (next_state, reward, done, info)
        """
        self.step_count += 1
        
        # Simulate uncertainty change based on action
        if action == KeyframeAction.CREATE_KEYFRAME:
            # Creating keyframe reduces uncertainty
            uncertainty_reduction = np.random.uniform(0.05, 0.15)
            self.uncertainty = max(0, self.uncertainty - uncertainty_reduction)
            
            # But increases energy need
            self.energy_need = min(1.0, self.energy_need + np.random.uniform(0.05, 0.1))
        else:
            # Skipping frame saves energy but increases uncertainty
            uncertainty_increase = np.random.uniform(0.02, 0.08)
            self.uncertainty = min(1.0, self.uncertainty + uncertainty_increase)
            
            # Energy need decreases when skipping
            self.energy_need = max(0, self.energy_need - np.random.uniform(0.05, 0.15))
            self.frames_skipped += 1
        
        # Stochastic drift in uncertainty
        self.uncertainty = np.clip(self.uncertainty + np.random.normal(0, 0.02), 0, 1)
        
        # Change battery mode occasionally
        if np.random.random() < 0.1:
            self.battery_mode = np.random.choice(['critical', 'low', 'moderate', 'good'])
        
        done = (self.step_count >= self.episode_length)
        
        # Reward signal
        reward = self._compute_reward(action)
        
        next_state = self.get_state()
        info = {
            'step': self.step_count,
            'done': done,
            'frames_skipped': self.frames_skipped
        }
        
        return next_state, reward, done, info
    
    def _compute_reward(self, action: KeyframeAction) -> float:
        """Compute reward for the action"""
        reward = 0.0
        
        if action == KeyframeAction.CREATE_KEYFRAME:
            # Reward for reducing uncertainty
            if self.uncertainty < 0.4:
                reward += 5.0  # Good accuracy
            elif self.uncertainty < 0.6:
                reward += 2.0  # Acceptable
            else:
                reward += 1.0  # Not ideal but created keyframe
            
            # Penalty for energy in critical/low battery
            if self.battery_mode in ['critical', 'low']:
                reward -= 3.0
            elif self.battery_mode == 'moderate':
                reward -= 1.0
        
        else:  # SKIP_FRAME
            # Reward for saving energy
            if self.battery_mode == 'critical':
                reward += 4.0
            elif self.battery_mode == 'low':
                reward += 2.0
            elif self.battery_mode == 'moderate':
                reward += 1.0
            
            # Penalty for high uncertainty
            if self.uncertainty > 0.7:
                reward -= 4.0
            elif self.uncertainty > 0.5:
                reward -= 1.0
        
        return np.clip(reward, -5.0, 5.0)


def train_rl_agent(episodes: int = 500, episode_length: int = 100,
                   learning_rate: float = 0.1, epsilon_decay: float = 0.995,
                   verbose: bool = True):
    """
    Train RL agent on simulated SLAM environment
    
    Args:
        episodes: Number of training episodes
        episode_length: Steps per episode
        learning_rate: Learning rate for Q-learning
        epsilon_decay: Epsilon decay rate for exploration
        verbose: Print training progress
    """
    
    print("=" * 80)
    print(" " * 20 + "RL AGENT TRAINING FOR KEYFRAME SELECTION")
    print("=" * 80)
    print(f"\nTraining Configuration:")
    print(f"  Episodes: {episodes}")
    print(f"  Episode Length: {episode_length}")
    print(f"  Learning Rate: {learning_rate}")
    print(f"  Epsilon Decay: {epsilon_decay}\n")
    
    # Initialize agent and environment
    agent = RLKeyframeSelector(learning_rate=learning_rate, discount_factor=0.95, 
                              epsilon=1.0, state_bins=10)
    env = SLAMSimulator(episode_length=episode_length)
    
    episode_rewards = []
    episode_keyframes = []
    episode_skipped = []
    
    print(f"{'Episode':<10} {'Reward':<12} {'KF Count':<12} {'Skipped':<12} {'Epsilon':<10}")
    print("-" * 80)
    
    for episode in range(episodes):
        state = env.reset()
        episode_reward = 0.0
        keyframe_count = 0
        prev_uncertainty = state['uncertainty']
        
        for step in range(episode_length):
            # Select action
            action = agent.select_action(
                state['uncertainty'],
                state['energy_need'],
                state['battery_mode'],
                training=True
            )
            
            # Execute action
            next_state, reward, done, info = env.step(action)
            
            # Learn from experience
            agent.learn_from_experience(
                state['uncertainty'],
                state['energy_need'],
                state['battery_mode'],
                prev_uncertainty,
                action == KeyframeAction.CREATE_KEYFRAME,
                next_state['uncertainty'],
                next_state['energy_need'],
                done
            )
            
            episode_reward += reward
            if action == KeyframeAction.CREATE_KEYFRAME:
                keyframe_count += 1
            prev_uncertainty = state['uncertainty']
            state = next_state
        
        # Decay epsilon
        agent.epsilon *= epsilon_decay
        agent.epsilon = max(agent.epsilon, 0.01)
        
        episode_rewards.append(episode_reward)
        episode_keyframes.append(keyframe_count)
        episode_skipped.append(env.frames_skipped)
        
        # Print progress
        if (episode + 1) % (episodes // 10) == 0:
            avg_reward = np.mean(episode_rewards[-20:])
            avg_kf = np.mean(episode_keyframes[-20:])
            avg_skip = np.mean(episode_skipped[-20:])
            print(f"{episode + 1:<10} {avg_reward:<12.2f} {avg_kf:<12.2f} {avg_skip:<12.2f} {agent.epsilon:<10.4f}")
    
    print("-" * 80)
    
    # Training complete
    print(f"\n✓ Training Complete!")
    print(f"\nFinal Statistics:")
    print(f"  Average Reward (last 20): {np.mean(episode_rewards[-20:]):.2f}")
    print(f"  Average Keyframes per Episode: {np.mean(episode_keyframes[-20:]):.2f}")
    print(f"  Average Frames Skipped per Episode: {np.mean(episode_skipped[-20:]):.2f}")
    print(f"  Q-Table States Explored: {len(agent.q_table)}")
    print(f"  Total Training Steps: {agent.training_steps}")
    
    return agent, episode_rewards, episode_keyframes, episode_skipped


def analyze_learned_policy(agent: RLKeyframeSelector):
    """Analyze and print the learned policy"""
    
    print("\n" + "=" * 80)
    print(" " * 25 + "LEARNED POLICY ANALYSIS")
    print("=" * 80)
    
    for battery_mode in ['critical', 'low', 'moderate', 'good']:
        agent.print_policy(battery_mode=battery_mode, top_n=5)
    
    print("\n" + "=" * 80)
    print(" " * 20 + "POLICY INSIGHTS")
    print("=" * 80)
    
    insights = {
        'critical': "When battery is critical, prefer SKIPPING frames to save energy",
        'low': "When battery is low, selectively skip high-uncertainty frames",
        'moderate': "When battery is moderate, balance between energy and accuracy",
        'good': "When battery is good, prioritize localization accuracy"
    }
    
    for mode, insight in insights.items():
        print(f"\n{mode.upper()}:")
        print(f"  → {insight}")


def main():
    parser = argparse.ArgumentParser(description='Train RL Agent for Keyframe Selection')
    parser.add_argument('--episodes', type=int, default=500,
                       help='Number of training episodes')
    parser.add_argument('--length', type=int, default=100,
                       help='Steps per episode')
    parser.add_argument('--lr', type=float, default=0.1,
                       help='Learning rate')
    parser.add_argument('--decay', type=float, default=0.995,
                       help='Epsilon decay rate')
    parser.add_argument('--output', default='rl_keyframe_model.json',
                       help='Output model file')
    args = parser.parse_args()
    
    # Train agent
    agent, rewards, keyframes, skipped = train_rl_agent(
        episodes=args.episodes,
        episode_length=args.length,
        learning_rate=args.lr,
        epsilon_decay=args.decay,
        verbose=True
    )
    
    # Analyze policy
    analyze_learned_policy(agent)
    
    # Save trained model
    print(f"\n💾 Saving trained model to {args.output}...")
    agent.save_model(args.output)
    
    # Save training curves
    training_data = {
        'episode_rewards': rewards,
        'episode_keyframes': keyframes,
        'episode_skipped': skipped,
        'config': {
            'episodes': args.episodes,
            'episode_length': args.length,
            'learning_rate': args.lr,
            'epsilon_decay': args.decay
        }
    }
    
    with open('rl_training_history.json', 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print("✓ Training history saved to rl_training_history.json")
    print("\n" + "=" * 80)
    print("✓ Training pipeline complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
