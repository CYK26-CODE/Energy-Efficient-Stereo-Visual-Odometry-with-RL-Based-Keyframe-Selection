#!/usr/bin/env python3
"""
Deep Q-Network Agent for Intelligent Keyframe Selection
Trains DQN to optimize keyframe creation vs energy consumption tradeoff
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random
import json
import os
from typing import Tuple, List, Dict


class DQNNetwork(nn.Module):
    """
    Deep Q-Network for keyframe selection
    Input: 7-element state vector
    Output: Q-values for 3 actions
    """
    
    def __init__(self, state_dim: int = 7, action_dim: int = 3, hidden_dim: int = 128):
        """
        Initialize DQN network
        
        Args:
            state_dim: State vector dimension (7)
            action_dim: Number of actions (3)
            hidden_dim: Hidden layer dimension (128)
        """
        super(DQNNetwork, self).__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        
        self.relu = nn.ReLU()
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        x = self.relu(self.fc1(state))
        x = self.relu(self.fc2(x))
        q_values = self.fc3(x)
        return q_values


class ReplayBuffer:
    """Experience replay buffer for DQN training"""
    
    def __init__(self, capacity: int = 100000):
        """
        Initialize replay buffer
        
        Args:
            capacity: Maximum buffer size
        """
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
    
    def push(self, state: np.ndarray, action: int, reward: float, 
             next_state: np.ndarray, done: bool):
        """Add experience to buffer"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple:
        """Sample random batch from buffer"""
        if len(self.buffer) < batch_size:
            return None
        
        batch = random.sample(self.buffer, batch_size)
        
        states = np.array([x[0] for x in batch])
        actions = np.array([x[1] for x in batch])
        rewards = np.array([x[2] for x in batch])
        next_states = np.array([x[3] for x in batch])
        dones = np.array([x[4] for x in batch])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self) -> int:
        return len(self.buffer)


class DQNAgent:
    """
    DQN Agent for keyframe selection
    Learns optimal policy for Save/Skip/Save-Light decisions
    """
    
    # Action definitions
    ACTION_SKIP = 0
    ACTION_SAVE_NORMAL = 1
    ACTION_SAVE_LIGHT = 2
    
    ACTION_NAMES = {
        0: "SKIP",
        1: "SAVE_NORMAL",
        2: "SAVE_LIGHT"
    }
    
    def __init__(self, state_dim: int = 7, action_dim: int = 3, 
                 learning_rate: float = 1e-4, gamma: float = 0.99,
                 epsilon_start: float = 0.3, epsilon_end: float = 0.05,
                 epsilon_decay_steps: int = 100000, device: str = 'cpu'):
        """
        Initialize DQN agent
        
        Args:
            state_dim: State vector dimension
            action_dim: Number of actions
            learning_rate: Adam optimizer learning rate
            gamma: Discount factor
            epsilon_start: Initial exploration rate
            epsilon_end: Final exploration rate
            epsilon_decay_steps: Steps over which epsilon decays
            device: 'cpu' or 'cuda'
        """
        self.device = torch.device(device)
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.learning_rate = learning_rate
        
        # Exploration schedule
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay_steps = epsilon_decay_steps
        self.epsilon = epsilon_start
        self.step_count = 0
        
        # Networks
        self.policy_net = DQNNetwork(state_dim, action_dim).to(self.device)
        self.target_net = DQNNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(capacity=100000)
        
        # Training statistics
        self.episode_rewards = []
        self.episode_lengths = []
        self.loss_history = []
        self.training_steps = 0
        self.target_update_freq = 1000
        
    def select_action(self, state: np.ndarray, training: bool = False) -> int:
        """
        Select action using ε-greedy policy
        
        Args:
            state: Current state vector
            training: Whether in training mode
            
        Returns:
            Action (0, 1, or 2)
        """
        if training and np.random.random() < self.epsilon:
            # Exploration: random action
            return np.random.randint(0, self.action_dim)
        else:
            # Exploitation: greedy action
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                action = q_values.max(1)[1].item()
            return action
    
    def store_experience(self, state: np.ndarray, action: int, reward: float,
                        next_state: np.ndarray, done: bool):
        """Store experience in replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)
    
    def train_step(self, batch_size: int = 64) -> float:
        """
        Perform one training step
        
        Args:
            batch_size: Batch size for training
            
        Returns:
            Loss value
        """
        if len(self.replay_buffer) < batch_size:
            return 0.0
        
        # Sample batch
        batch = self.replay_buffer.sample(batch_size)
        if batch is None:
            return 0.0
        
        states, actions, rewards, next_states, dones = batch
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Current Q-values
        q_values = self.policy_net(states)
        q_values = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Target Q-values (Double DQN)
        with torch.no_grad():
            next_q_values = self.target_net(next_states)
            next_actions = self.policy_net(next_states).argmax(1)
            next_q_values = next_q_values.gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Clip rewards for stability
        target_q_values = torch.clamp(target_q_values, -50, 50)
        
        # Loss
        loss = nn.MSELoss()(q_values, target_q_values)
        
        # Optimization step
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        self.training_steps += 1
        self.loss_history.append(loss.item())
        
        # Update target network
        if self.training_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Update epsilon
        self._update_epsilon()
        
        return loss.item()
    
    def _update_epsilon(self):
        """Update epsilon following linear decay schedule"""
        if self.step_count < self.epsilon_decay_steps:
            self.epsilon = (self.epsilon_start - self.epsilon_end) * \
                          (1 - self.step_count / self.epsilon_decay_steps) + self.epsilon_end
        else:
            self.epsilon = self.epsilon_end
        self.step_count += 1
    
    def end_episode(self, episode_reward: float, episode_length: int):
        """Record episode statistics"""
        self.episode_rewards.append(episode_reward)
        self.episode_lengths.append(episode_length)
    
    def save_model(self, filepath: str):
        """Save model checkpoint"""
        checkpoint = {
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'training_steps': self.training_steps,
            'step_count': self.step_count,
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'loss_history': self.loss_history,
            'hyperparameters': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'learning_rate': self.learning_rate,
                'gamma': self.gamma,
                'epsilon_start': self.epsilon_start,
                'epsilon_end': self.epsilon_end,
                'epsilon_decay_steps': self.epsilon_decay_steps
            }
        }
        torch.save(checkpoint, filepath)
        print(f"✓ DQN model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model checkpoint"""
        if not os.path.exists(filepath):
            print(f"⚠ Model file not found: {filepath}")
            return False
        
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.training_steps = checkpoint.get('training_steps', 0)
        self.step_count = checkpoint.get('step_count', 0)
        self.epsilon = checkpoint.get('epsilon', self.epsilon_end)
        self.episode_rewards = checkpoint.get('episode_rewards', [])
        self.episode_lengths = checkpoint.get('episode_lengths', [])
        self.loss_history = checkpoint.get('loss_history', [])
        
        print(f"✓ DQN model loaded from {filepath}")
        print(f"  Training steps: {self.training_steps}")
        print(f"  Episodes completed: {len(self.episode_rewards)}")
        return True
    
    def get_summary(self) -> Dict:
        """Get training summary"""
        return {
            'training_steps': self.training_steps,
            'episodes_completed': len(self.episode_rewards),
            'avg_reward_last_20': np.mean(self.episode_rewards[-20:]) if self.episode_rewards else 0,
            'avg_length_last_20': np.mean(self.episode_lengths[-20:]) if self.episode_lengths else 0,
            'buffer_size': len(self.replay_buffer),
            'epsilon': self.epsilon,
            'avg_loss_last_100': np.mean(self.loss_history[-100:]) if self.loss_history else 0
        }
