#!/usr/bin/env python3
"""
RL Agent Training Application
Train the reinforcement learning agent for keyframe selection
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app' / 'runtime'))

from train_rl_agent import train_rl_agent, SLAMSimulator
from rl_keyframe_selector import RLKeyframeSelector


def main():
    print("="*80)
    print(" "*25 + "RL AGENT TRAINER")
    print("="*80)
    print("\nThis application trains the RL agent for intelligent keyframe selection.")
    print("Training uses a simulated SLAM environment.")
    print("\nRecommended settings:")
    print("  - Episodes: 500-1000 (more = better policy)")
    print("  - Episode length: 100 steps")
    print("  - Learning rate: 0.1")
    print("  - Epsilon decay: 0.995")
    print("\n" + "="*80)
    
    # Get user input
    try:
        episodes = int(input("\nNumber of training episodes [500]: ") or "500")
        episode_length = int(input("Steps per episode [100]: ") or "100")
        learning_rate = float(input("Learning rate [0.1]: ") or "0.1")
        epsilon_decay = float(input("Epsilon decay [0.995]: ") or "0.995")
    except ValueError:
        print("\n❌ Invalid input, using defaults")
        episodes = 500
        episode_length = 100
        learning_rate = 0.1
        epsilon_decay = 0.995
    
    print(f"\n🚀 Starting training with:")
    print(f"   Episodes: {episodes}")
    print(f"   Episode length: {episode_length}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Epsilon decay: {epsilon_decay}\n")
    
    # Train
    train_rl_agent(
        episodes=episodes,
        episode_length=episode_length,
        learning_rate=learning_rate,
        epsilon_decay=epsilon_decay,
        verbose=True
    )
    
    print("\n" + "="*80)
    print("✓ Training complete!")
    print("  Model saved to: rl_keyframe_model.json")
    print("  You can now use this trained model in the SLAM system")
    print("="*80)
    
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
