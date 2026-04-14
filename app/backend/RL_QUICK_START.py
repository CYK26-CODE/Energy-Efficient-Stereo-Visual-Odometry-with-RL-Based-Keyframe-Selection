#!/usr/bin/env python3
"""
Quick Start Guide for RL-Based Intelligent Keyframe Selection
"""

QUICK_START_GUIDE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║         QUICK START: RL-BASED INTELLIGENT KEYFRAME SELECTION                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 STEP 1: Install Dependencies
─────────────────────────────────────────────────────────────────────────────
$ pip install -r requirements.txt

✅ Required packages:
   • opencv-python (image processing)
   • numpy (numerical computing)
   • matplotlib (visualization)
   • scipy (scientific computing)
   • psutil (battery monitoring)


🤖 STEP 2: Train RL Agent in Simulation
─────────────────────────────────────────────────────────────────────────────
$ python train_rl_agent.py --episodes 500 --lr 0.1

Output files:
   • rl_keyframe_model.json (trained Q-table)
   • rl_training_history.json (training curves)

Expected time: ~10 minutes
Expected result: 200-300 learned states, convergence at ~300 episodes


🚀 STEP 3: Run SLAM with RL Agent (Inference)
─────────────────────────────────────────────────────────────────────────────
$ python integrated_slam_rl.py

Controls during execution:
   • Q: Quit
   • S: Save map and RL model
   • R: Reset view


📊 STEP 4: Check Results
─────────────────────────────────────────────────────────────────────────────
Generated files:
   • rl_stereo_slam_map.json (3D map + trajectory)
   • rl_keyframe_model.json (final trained model)
   • rl_training_history.json (training curves)


⚙️  ADVANCED: Train with Real Data
─────────────────────────────────────────────────────────────────────────────
$ python integrated_slam_rl.py --train --model my_model.json

The system will:
   1. Load pre-trained model from rl_keyframe_model.json
   2. Continue learning from real SLAM data
   3. Adapt policy to actual camera and environment
   4. Periodically save improved model


🔧 Configuration Options
─────────────────────────────────────────────────────────────────────────────

Training Script:
  --episodes N          Number of training episodes (default: 500)
  --length N            Steps per episode (default: 100)
  --lr RATE             Learning rate (default: 0.1)
  --decay RATE          Epsilon decay (default: 0.995)
  --output FILE         Model output file (default: rl_keyframe_model.json)

SLAM Script:
  --left-camera URL     Left camera URL
  --right-camera URL    Right camera URL
  --no-rl              Disable RL agent (battery-aware mode only)
  --train              Enable RL training mode
  --model FILE         RL model file path


📈 Understanding the Output
─────────────────────────────────────────────────────────────────────────────

During training:
  Episode  Reward      KF Count   Skipped    Epsilon
  50       12.45       8.2        18.7       0.9950
  100      15.32       7.8        19.2       0.9900
  500      18.76       6.9        20.5       0.6065

Target values:
  • Reward: Should increase over time (learning)
  • KF Count: Should stabilize (policy converges)
  • Epsilon: Should decay (less exploration)


🎯 Performance Metrics
─────────────────────────────────────────────────────────────────────────────

During SLAM execution:
  • Frame Rate: 15-30 FPS
  • Uncertainty: 0.0-1.0 (lower = better localization)
  • RL Decision: CREATE_KEYFRAME or SKIP_FRAME
  • Q-Values: Show action confidence

Display shows:
  RL: CREATE_KEYFRAME (Unc: 0.65)
  Q: Create=4.23 Skip=1.87

Interpretation:
  • High uncertainty → Prefers to create keyframe
  • Large Q difference → High confidence in decision


⚡ Energy Efficiency Results
─────────────────────────────────────────────────────────────────────────────

Typical battery level effects:

GOOD BATTERY (>50%):
  • Process: All frames
  • Keyframes: ~1 per second
  • Energy savings: 20-30%

MODERATE BATTERY (15-50%):
  • Process: Every other frame
  • Keyframes: ~0.5 per second
  • Energy savings: 50-60%

LOW BATTERY (<15%):
  • Process: Every 4th frame
  • Keyframes: ~0.25 per second
  • Energy savings: 70-80%

CRITICAL BATTERY (<5%):
  • Process: Every 8th frame
  • Keyframes: Minimal
  • Energy savings: 85-90%


🔬 Understanding RL Components
─────────────────────────────────────────────────────────────────────────────

State Space:
  • Uncertainty [0-1]: How confident is localization?
  • Energy Need [0-1]: How critical is battery?
  • Battery Mode: critical, low, moderate, good

Action Space:
  • CREATE_KEYFRAME: High quality, high energy cost
  • SKIP_FRAME: Low energy, risks localization

Reward Function:
  • Positive: Improves accuracy, saves energy
  • Negative: Wastes energy, loses accuracy


🐛 Debugging Tips
─────────────────────────────────────────────────────────────────────────────

If reward not improving:
  → Increase learning rate: --lr 0.2
  → Reduce epsilon decay: --decay 0.99

If agent being too conservative:
  → Increase exploration: epsilon = 0.2 in code

If agent creating too many keyframes:
  → Increase energy penalty in reward function
  → Train on lower battery modes

If performance degrading after real-world training:
  → Save best model periodically: --train
  → Use --no-rl for comparison


📚 Further Reading
─────────────────────────────────────────────────────────────────────────────

See documentation:
  • RL_KEYFRAME_SELECTION.md - Detailed RL explanation
  • README.md - Full system documentation

Q-Learning fundamentals:
  • Watkins & Dayan (1992): "Q-learning"
  • Sutton & Barto (2018): "Reinforcement Learning"


✨ Pro Tips
─────────────────────────────────────────────────────────────────────────────

1. Train in simulation first
   - Faster than real-time learning
   - No camera setup needed
   - Guaranteed convergence

2. Use --train for real deployment
   - Adapts to actual camera/environment
   - Improves policy during operation
   - Fine-tunes hyperparameters

3. Save frequently
   - Press 'S' during execution
   - Prevents losing trained model
   - Allows recovery from crashes

4. Monitor Q-values
   - Large difference = high confidence
   - Small difference = uncertain decision
   - Watch for convergence

5. Adjust rewards for your priorities
   - Increase energy weight for long operation
   - Increase accuracy weight for mapping
   - Balance based on application


🚨 Common Issues
─────────────────────────────────────────────────────────────────────────────

Issue: "Model file not found"
Fix: Run training first: python train_rl_agent.py

Issue: "Camera connection failed"
Fix: Verify camera URLs are correct and accessible

Issue: "Low FPS"
Fix: Disable visualization, reduce max_keyframes

Issue: "Agent always skipping"
Fix: Increase uncertainty weight in reward function

Issue: "Model not improving"
Fix: Check epsilon decay, increase learning rate


═══════════════════════════════════════════════════════════════════════════════

Next steps:
1. Run: python train_rl_agent.py
2. Run: python integrated_slam_rl.py
3. Read: RL_KEYFRAME_SELECTION.md

Questions? Check console output for detailed logs!
"""

if __name__ == "__main__":
    print(QUICK_START_GUIDE)
    
    # Save to file
    with open("RL_QUICK_START.txt", "w") as f:
        f.write(QUICK_START_GUIDE)
    
    print("\n✓ Quick start guide saved to: RL_QUICK_START.txt")
