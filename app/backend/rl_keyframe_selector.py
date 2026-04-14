#!/usr/bin/env python3
"""
Reinforcement Learning Agent for Intelligent Keyframe Selection
Balances localization uncertainty vs. energy consumption trade-off
Uses Q-learning to learn optimal keyframe selection policies
"""

import numpy as np
import json
from collections import defaultdict, deque
from typing import Tuple, Dict, List, Optional
from enum import Enum
import pickle
import os


class KeyframeAction(Enum):
    """Actions the RL agent can take"""
    SKIP_FRAME = 0          # Don't create keyframe (save energy)
    CREATE_KEYFRAME = 1     # Create keyframe (improve localization)


class LocalizationUncertaintyMetrics:
    """Compute localization uncertainty metrics for the current state"""
    
    def __init__(self):
        """Initialize uncertainty metrics tracker"""
        self.position_variance = 0.0
        self.rotation_variance = 0.0
        self.feature_match_confidence = 1.0
        self.tracking_error = 0.0
        
    def update_from_slam(self, slam_system) -> float:
        """
        Update uncertainty metrics from SLAM system
        Returns normalized uncertainty score [0, 1]
        """
        try:
            # Get trajectory uncertainty (position variance)
            trajectory = slam_system.get_trajectory()
            if len(trajectory) > 5:
                recent_positions = trajectory[-5:]
                self.position_variance = float(np.var(recent_positions))
            
            # Get keyframe info
            kf_info = slam_system.get_keyframes_info()
            
            # Calculate tracking uncertainty based on point density
            total_points = kf_info.get('total_points', 1)
            total_keyframes = kf_info.get('total_keyframes', 1)
            points_per_kf = total_points / max(total_keyframes, 1)
            
            # Lower points per keyframe = higher uncertainty
            if points_per_kf < 100:
                self.tracking_error = 1.0 - (points_per_kf / 100.0)
            else:
                self.tracking_error = 0.0
            
            # Feature match confidence (inverse of loop closure need)
            loop_closures = kf_info.get('loop_closures', 0)
            frames_processed = kf_info.get('frames_processed', 1)
            
            # High loop closures indicate drift issues
            self.feature_match_confidence = max(0, 1.0 - (loop_closures / max(frames_processed / 100, 1)))
            
            # Combined normalized uncertainty [0, 1]
            uncertainty = (
                min(self.position_variance, 1.0) * 0.3 +
                self.tracking_error * 0.4 +
                (1.0 - self.feature_match_confidence) * 0.3
            )
            
            return min(max(uncertainty, 0.0), 1.0)
            
        except Exception as e:
            return 0.5  # Default to medium uncertainty on error


class EnergyModel:
    """Model energy consumption based on SLAM operations"""
    
    def __init__(self):
        """Initialize energy model"""
        self.base_consumption = 1.0  # Base power for camera/processing
        self.keyframe_cost = 5.0     # Energy cost of creating keyframe
        self.bundle_adj_cost = 3.0   # Energy cost of bundle adjustment
        self.viz_cost = 2.0          # Energy cost of visualization
        
    def estimate_energy_reduction(self, battery_mode: str) -> float:
        """
        Estimate energy savings from skipping keyframe
        Returns normalized energy savings [0, 1]
        """
        mode_multiplier = {
            'critical': 1.0,   # Maximum savings needed
            'low': 0.8,
            'moderate': 0.5,
            'good': 0.2        # Minimal energy savings needed
        }
        return mode_multiplier.get(battery_mode, 0.5)


class RLKeyframeSelector:
    """
    Q-Learning based agent for intelligent keyframe selection
    Learns optimal policy balancing localization accuracy vs. energy
    """
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95,
                 epsilon: float = 0.1, state_bins: int = 10):
        """
        Initialize RL agent
        
        Args:
            learning_rate: Alpha parameter for Q-learning updates
            discount_factor: Gamma parameter for future rewards
            epsilon: Exploration vs exploitation trade-off
            state_bins: Number of bins for discretizing continuous state space
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.state_bins = state_bins
        
        # Q-table: (uncertainty_bin, energy_bin, battery_mode) -> action_value
        self.q_table = defaultdict(lambda: {
            KeyframeAction.SKIP_FRAME: 0.0,
            KeyframeAction.CREATE_KEYFRAME: 0.0
        })
        
        # Experience replay buffer
        self.experience_buffer = deque(maxlen=1000)
        
        # Training statistics
        self.episode_rewards = []
        self.episode_keyframes = []
        self.training_steps = 0
        
        # Initialize uncertainty and energy models
        self.uncertainty_metrics = LocalizationUncertaintyMetrics()
        self.energy_model = EnergyModel()
    
    def discretize_state(self, uncertainty: float, energy_need: float) -> Tuple[int, int]:
        """
        Discretize continuous state values into bins
        
        Args:
            uncertainty: Localization uncertainty [0, 1]
            energy_need: Energy reduction need [0, 1]
            
        Returns:
            (uncertainty_bin, energy_bin)
        """
        uncertainty_bin = min(int(uncertainty * self.state_bins), self.state_bins - 1)
        energy_bin = min(int(energy_need * self.state_bins), self.state_bins - 1)
        return uncertainty_bin, energy_bin
    
    def get_state_key(self, uncertainty_bin: int, energy_bin: int, battery_mode: str) -> Tuple:
        """Create state key for Q-table lookup"""
        return (uncertainty_bin, energy_bin, battery_mode)
    
    def select_action(self, uncertainty: float, energy_need: float,
                     battery_mode: str, training: bool = True) -> KeyframeAction:
        """
        Select action using epsilon-greedy policy
        
        Args:
            uncertainty: Localization uncertainty [0, 1]
            energy_need: Energy reduction need [0, 1]
            battery_mode: Current battery mode
            training: Whether in training mode (use epsilon-greedy)
            
        Returns:
            Selected action (SKIP_FRAME or CREATE_KEYFRAME)
        """
        uncertainty_bin, energy_bin = self.discretize_state(uncertainty, energy_need)
        state_key = self.get_state_key(uncertainty_bin, energy_bin, battery_mode)
        
        # Epsilon-greedy exploration
        if training and np.random.random() < self.epsilon:
            return KeyframeAction(np.random.randint(0, 2))
        
        # Exploit: choose action with highest Q-value
        q_values = self.q_table[state_key]
        max_q = max(q_values.values())
        
        # Get all actions with maximum Q-value
        best_actions = [action for action, q in q_values.items() if q == max_q]
        return np.random.choice(best_actions)
    
    def compute_reward(self, action: KeyframeAction, uncertainty: float,
                      energy_need: float, prev_uncertainty: float,
                      keyframe_created: bool) -> float:
        """
        Compute reward signal for the action taken
        
        Args:
            action: Action taken
            uncertainty: Current localization uncertainty
            energy_need: Current energy reduction need
            prev_uncertainty: Previous uncertainty
            keyframe_created: Whether keyframe was actually created
            
        Returns:
            Reward signal
        """
        reward = 0.0
        
        # Reward for improving localization (uncertainty reduction)
        uncertainty_improvement = max(0, prev_uncertainty - uncertainty)
        localization_reward = uncertainty_improvement * 10.0
        
        if action == KeyframeAction.CREATE_KEYFRAME:
            # Penalize energy usage
            energy_penalty = -energy_need * 5.0
            
            # Bonus if keyframe was actually needed (high uncertainty)
            if uncertainty > 0.5:
                localization_reward += 5.0
            else:
                localization_reward -= 3.0  # Penalty for unnecessary keyframe
            
            reward = localization_reward + energy_penalty
            
        else:  # SKIP_FRAME
            # Reward for energy savings
            energy_reward = energy_need * 3.0
            
            # Penalty if uncertainty is high and we skip (missed opportunity)
            if uncertainty > 0.6:
                energy_reward -= 5.0
            
            reward = energy_reward
        
        # Clamp reward to reasonable range
        return np.clip(reward, -10.0, 10.0)
    
    def update_q_value(self, state_key: Tuple, action: KeyframeAction,
                       reward: float, next_state_key: Tuple, done: bool = False):
        """
        Update Q-value using Q-learning update rule
        
        Args:
            state_key: Current state key
            action: Action taken
            reward: Reward received
            next_state_key: Next state key
            done: Whether episode is done
        """
        current_q = self.q_table[state_key][action]
        
        if done:
            max_next_q = 0.0
        else:
            max_next_q = max(self.q_table[next_state_key].values())
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state_key][action] = new_q
        
        self.training_steps += 1
    
    def learn_from_experience(self, uncertainty: float, energy_need: float,
                             battery_mode: str, prev_uncertainty: float,
                             keyframe_created: bool, next_uncertainty: float,
                             next_energy_need: float, done: bool = False):
        """
        Learn from a single experience
        
        Args:
            uncertainty: Initial uncertainty
            energy_need: Initial energy need
            battery_mode: Battery mode
            prev_uncertainty: Previous uncertainty (for comparison)
            keyframe_created: Whether keyframe was created
            next_uncertainty: Next uncertainty state
            next_energy_need: Next energy need
            done: Whether episode is done
        """
        # Discretize states
        uncertainty_bin, energy_bin = self.discretize_state(uncertainty, energy_need)
        state_key = self.get_state_key(uncertainty_bin, energy_bin, battery_mode)
        
        next_uncertainty_bin, next_energy_bin = self.discretize_state(next_uncertainty, next_energy_need)
        next_state_key = self.get_state_key(next_uncertainty_bin, next_energy_bin, battery_mode)
        
        # Determine action (assume CREATE_KEYFRAME if keyframe was created)
        action = KeyframeAction.CREATE_KEYFRAME if keyframe_created else KeyframeAction.SKIP_FRAME
        
        # Compute reward
        reward = self.compute_reward(action, uncertainty, energy_need, prev_uncertainty, keyframe_created)
        
        # Update Q-value
        self.update_q_value(state_key, action, reward, next_state_key, done)
        
        # Store in experience buffer
        self.experience_buffer.append((state_key, action, reward, next_state_key, done))
    
    def get_policy_summary(self) -> Dict:
        """
        Get summary of learned policy
        
        Returns:
            Dictionary with policy statistics
        """
        summary = {
            'training_steps': self.training_steps,
            'q_table_size': len(self.q_table),
            'states_explored': len(self.q_table),
            'avg_episode_reward': np.mean(self.episode_rewards[-100:]) if self.episode_rewards else 0,
            'avg_keyframes_per_episode': np.mean(self.episode_keyframes[-100:]) if self.episode_keyframes else 0,
        }
        return summary
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        model_data = {
            'q_table': dict(self.q_table),
            'training_steps': self.training_steps,
            'episode_rewards': list(self.episode_rewards),
            'episode_keyframes': list(self.episode_keyframes),
            'hyperparameters': {
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'epsilon': self.epsilon,
                'state_bins': self.state_bins
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2, default=str)
        
        print(f"✓ RL model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            # Restore Q-table
            self.q_table = defaultdict(lambda: {
                KeyframeAction.SKIP_FRAME: 0.0,
                KeyframeAction.CREATE_KEYFRAME: 0.0
            })
            
            for state_key_str, actions in model_data['q_table'].items():
                # Convert string keys back to tuples
                state_key = eval(state_key_str)
                for action_name, q_value in actions.items():
                    action = KeyframeAction[action_name] if isinstance(action_name, str) else action_name
                    self.q_table[state_key][action] = q_value
            
            self.training_steps = model_data.get('training_steps', 0)
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_keyframes = model_data.get('episode_keyframes', [])
            
            print(f"✓ RL model loaded from {filepath}")
            print(f"  Training steps: {self.training_steps}")
            print(f"  States explored: {len(self.q_table)}")
            
        except FileNotFoundError:
            print(f"⚠ Model file not found: {filepath}")
        except Exception as e:
            print(f"⚠ Error loading model: {str(e)}")
    
    def print_policy(self, battery_mode: str = 'good', top_n: int = 5):
        """
        Print learned policy for analysis
        
        Args:
            battery_mode: Battery mode to analyze
            top_n: Number of top states to show
        """
        print(f"\n📊 RL Policy for Battery Mode: {battery_mode.upper()}")
        print("=" * 80)
        
        # Find states for this battery mode
        states_for_mode = [
            (state_key, self.q_table[state_key])
            for state_key in self.q_table.keys()
            if state_key[2] == battery_mode
        ]
        
        if not states_for_mode:
            print(f"No states explored for battery mode: {battery_mode}")
            return
        
        # Sort by max Q-value difference (importance)
        states_for_mode.sort(
            key=lambda x: abs(x[1][KeyframeAction.CREATE_KEYFRAME] - x[1][KeyframeAction.SKIP_FRAME]),
            reverse=True
        )
        
        print(f"{'Unc.Bin':<8} {'Eng.Bin':<8} {'Create KF':<12} {'Skip Frame':<12} {'Action':<15}")
        print("-" * 80)
        
        for state_key, q_values in states_for_mode[:top_n]:
            unc_bin, eng_bin, _ = state_key
            q_create = q_values[KeyframeAction.CREATE_KEYFRAME]
            q_skip = q_values[KeyframeAction.SKIP_FRAME]
            
            best_action = "CREATE KF" if q_create > q_skip else "SKIP FRAME"
            
            print(f"{unc_bin:<8} {eng_bin:<8} {q_create:<12.3f} {q_skip:<12.3f} {best_action:<15}")


class RL_SLAM_Integration:
    """Integration of RL agent with SLAM system"""
    
    def __init__(self, slam_system, rl_agent: RLKeyframeSelector):
        """
        Initialize RL-SLAM integration
        
        Args:
            slam_system: StereoSLAMSystem instance
            rl_agent: RLKeyframeSelector instance
        """
        self.slam_system = slam_system
        self.rl_agent = rl_agent
        
        self.prev_uncertainty = 0.5
        self.prev_energy_need = 0.5
        self.episode_keyframes = 0
        self.episode_reward = 0.0
    
    def decide_keyframe_creation(self, battery_mode: str, training: bool = True) -> Tuple[bool, Dict]:
        """
        Decide whether to create keyframe using RL policy
        
        Args:
            battery_mode: Current battery mode
            training: Whether in training mode
            
        Returns:
            (should_create_keyframe, stats_dict)
        """
        # Get current state from SLAM system
        uncertainty = self.rl_agent.uncertainty_metrics.update_from_slam(self.slam_system)
        energy_need = self.rl_agent.energy_model.estimate_energy_reduction(battery_mode)
        
        # Select action using RL policy
        action = self.rl_agent.select_action(uncertainty, energy_need, battery_mode, training)
        
        should_create_keyframe = (action == KeyframeAction.CREATE_KEYFRAME)
        
        # Learn from this experience
        if training and hasattr(self, '_next_uncertainty'):
            next_uncertainty = self._next_uncertainty
            next_energy_need = self._next_energy_need
            self.rl_agent.learn_from_experience(
                uncertainty, energy_need, battery_mode,
                self.prev_uncertainty, should_create_keyframe,
                next_uncertainty, next_energy_need
            )
        
        # Store current state for next learning step
        self.prev_uncertainty = uncertainty
        self.prev_energy_need = energy_need
        
        stats = {
            'uncertainty': uncertainty,
            'energy_need': energy_need,
            'action': action.name,
            'should_create_keyframe': should_create_keyframe,
            'q_create': self.rl_agent.q_table[
                self.rl_agent.get_state_key(*self.rl_agent.discretize_state(uncertainty, energy_need), battery_mode)
            ][KeyframeAction.CREATE_KEYFRAME],
            'q_skip': self.rl_agent.q_table[
                self.rl_agent.get_state_key(*self.rl_agent.discretize_state(uncertainty, energy_need), battery_mode)
            ][KeyframeAction.SKIP_FRAME]
        }
        
        return should_create_keyframe, stats
