# Integrated Stereo SLAM System - Final Build

## Overview
A complete, production-ready Stereo SLAM (Simultaneous Localization and Mapping) system with advanced features including:
- Real-time stereo vision processing
- Loop closure detection
- Bundle adjustment optimization
- Live 3D visualization
- **Battery-aware dynamic keyframe management** (Power-efficient frame skipping)
- **Reinforcement Learning-based intelligent keyframe selection** (Learns optimal energy-accuracy trade-off)

## Features

### Core SLAM Capabilities
- **Stereo Vision**: Processes dual camera streams for 3D reconstruction
- **Feature Extraction**: Advanced SIFT-based feature detection and matching
- **Visual Odometry**: Estimates camera motion between frames
- **Loop Closure Detection**: Identifies and corrects drift in trajectories
- **Bundle Adjustment**: Optimizes camera poses and 3D points for accuracy

### Battery-Aware Optimization
- **Dynamic Frame Skipping**: Intelligently skips redundant frames based on battery level
  - Critical (<5%): Process every 8th frame
  - Low (<15%): Process every 4th frame
  - Moderate (<50%): Process every other frame
  - Good (≥50%): Process all frames
- **Adaptive Keyframe Threshold**: Adjusts displacement requirement for keyframe creation
- **Smart Bundle Adjustment**: Reduces optimization frequency when battery is low

### RL-Based Intelligent Keyframe Selection (NEW)
- **Q-Learning Agent**: Learns optimal keyframe creation policy
- **Multi-Objective Optimization**: Balances localization accuracy vs. energy consumption
- **Uncertainty-Aware**: Considers localization confidence in decisions
- **Adaptive Policy**: Different strategies for different battery levels
- **Training & Inference**: Pre-train in simulation, fine-tune on real data

### UI Features
- Real-time dual camera display
- Live 3D point cloud visualization
- Statistics panel with battery status
- RL decision visualization (uncertainty, Q-values)
- Color-coded battery indicator (Green → Yellow → Orange → Red)
- Performance metrics (FPS, keyframes, points)

## File Structure

```
final/
├── integrated_slam.py              # Main SLAM application with battery management
├── integrated_slam_rl.py           # SLAM with RL-based keyframe selection (NEW)
├── stereo_slam.py                  # Core SLAM system implementation
├── camera_stream_handler.py        # Camera streaming and frame capture
├── advanced_features.py            # Feature extraction and matching
├── visual_odometry.py              # Visual odometry engine
├── stereo_vision.py                # Stereo vision pipeline
├── rl_keyframe_selector.py         # RL agent for intelligent keyframe selection (NEW)
├── train_rl_agent.py               # RL training script (NEW)
├── camera_calibration.json         # Camera calibration parameters
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── RL_KEYFRAME_SELECTION.md        # RL system documentation (NEW)
└── rl_keyframe_model.json          # Trained RL model (generated)
```

## Installation

### Prerequisites
- Python 3.7+
- OpenCV with extra modules
- CUDA (optional, for GPU acceleration)

### Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Camera Calibration**
   - Ensure `camera_calibration.json` contains valid calibration parameters
   - Update if using different cameras

## Usage

### Basic Run (Original Battery-Aware Mode)
```bash
python integrated_slam.py
```

### Run with RL Agent (Inference Mode)
```bash
python integrated_slam_rl.py
```

### Train RL Agent in Simulation
```bash
python train_rl_agent.py --episodes 500 --length 100
```

### Run with RL Agent Training (Continues Learning)
```bash
python integrated_slam_rl.py --train --model my_model.json
```

### Disable RL and use Battery-Aware Only
```bash
python integrated_slam_rl.py --no-rl
```

### With Custom Camera URLs
```bash
python integrated_slam_rl.py \
  --left-camera http://192.168.1.37/stream \
  --right-camera http://192.168.1.38/stream
```

### Controls During Execution
- **Q**: Quit the application
- **S**: Save current SLAM map and RL model
- **R**: Reset visualization view

## RL-Based Intelligent Keyframe Selection

### How It Works
1. **Learning Phase**: Train RL agent on simulated SLAM environment to learn optimal policy
2. **Deployment Phase**: Use learned policy to make real-time keyframe decisions
3. **Continuous Learning**: Optionally continue training on real SLAM data

### Training the RL Agent
```bash
# Train in simulation (recommended for first time)
python train_rl_agent.py --episodes 500

# Expected output:
# - rl_keyframe_model.json: Trained Q-table
# - rl_training_history.json: Training curves and statistics
```

### RL Agent Configuration
The agent learns from:
- **State**: Localization uncertainty + energy need + battery mode
- **Actions**: Create keyframe or skip frame
- **Reward**: Multi-objective: accuracy vs. energy

### Example Results
After training:
- **States Learned**: 200-300 unique states
- **Convergence Time**: ~300 episodes
- **Energy Savings**: 20-80% depending on battery level
- **Accuracy Maintained**: ±5-10% vs. non-RL version

For detailed RL information, see `RL_KEYFRAME_SELECTION.md`

## Output

### Console Output
- Real-time frame processing statistics
- Keyframe creation notifications
- Loop closure detection alerts
- Battery state and frame skipping information
- RL decision information (uncertainty, Q-values)

### Generated Files
- **integrated_stereo_slam_map.json**: Complete SLAM map with:
  - 3D point cloud
  - Camera trajectory
  - Point cloud colors
  - Loop closures
  - Frame statistics
- **rl_stereo_slam_map.json**: SLAM map generated with RL agent
- **rl_keyframe_model.json**: Trained RL model (Q-table)
- **rl_training_history.json**: Training statistics and curves

## Camera Configuration

Default camera URLs (configurable):
- **Left Camera**: `http://192.168.1.37/stream`
- **Right Camera**: `http://192.168.1.38/stream`

For local video files or different sources, modify the URL format in the command line arguments.

## Performance Optimization

### Battery-Aware Tuning
The system automatically adjusts for optimal performance based on battery state:

| Battery Level | Mode | Frame Processing | Keyframe Threshold | Bundle Adjustment |
|---------------|------|------------------|--------------------|-------------------|
| <5% | Critical | Every 8th | 3x multiplier | Every 20 keyframes |
| 5-15% | Low | Every 4th | 2x multiplier | Every 10 keyframes |
| 15-50% | Moderate | Every 2nd | 1.5x multiplier | Every 10 keyframes |
| >50% | Good | All frames | 1x multiplier | Every 5 keyframes |

### RL-Based Tuning
The RL agent learns policies that:
- Prioritize energy savings in critical battery
- Maintain accuracy in good battery conditions
- Adapt to current localization uncertainty
- Learn from multiple battery modes simultaneously

### Hardware Requirements
- **GPU**: NVIDIA GPU with CUDA support (optional)
- **CPU**: Multi-core processor recommended
- **Memory**: 4GB+ RAM
- **Storage**: 50MB for typical session

## Troubleshooting

### Camera Connection Issues
- Verify camera URLs are accessible
- Check network connectivity
- Ensure cameras support MJPEG streaming

### Performance Issues
- Reduce feature extraction threshold
- Disable visualization for faster processing
- Reduce max keyframes limit

### RL Training Issues
- Ensure `rl_training_history.json` shows convergence
- If reward not improving: increase learning rate to 0.2
- If too conservative: increase epsilon to 0.15
- If overfitting to battery mode: train on more diverse episodes

### Memory Issues
- Limit the maximum keyframes (default: 100)
- Reduce point cloud density
- Enable frame skipping manually

## Technical Details

### Dependencies
- `cv2` (OpenCV): Computer vision operations
- `numpy`: Numerical computations
- `matplotlib`: 3D visualization
- `psutil`: Battery state monitoring
- `scipy`: Scientific computing

### Key Parameters
- `max_keyframes`: 100 (maximum stored keyframes)
- `min_displacement`: 0.05m (minimum movement for new keyframe)
- `loop_closure_threshold`: 0.75 (similarity threshold for loop detection)

## Advanced Configuration

Edit these parameters in `integrated_slam.py` for custom behavior:

```python
self.slam_system = StereoSLAMSystem(
    max_keyframes=100,              # Increase for larger environments
    min_displacement=0.05,          # Decrease for more keyframes
    loop_closure_threshold=0.75     # Increase to be stricter
)
```

## Performance Metrics

Expected performance on mid-range hardware:
- **Frame Rate**: 15-30 FPS (dependent on resolution)
- **Keyframe Rate**: 1-2 keyframes per second
- **3D Points**: Up to 50,000+ points
- **Memory Usage**: 500MB - 2GB
- **Power Efficiency**: 30-80% frame reduction at low battery

## References

### Key Concepts
- **SLAM**: Simultaneous Localization and Mapping
- **Bundle Adjustment**: Non-linear optimization of camera poses and 3D points
- **Loop Closure**: Detecting revisited locations to correct accumulated drift
- **Visual Odometry**: Estimating motion from visual features

## License

This is a research/educational implementation of stereo SLAM.

## Support

For issues or questions:
1. Check console output for error messages
2. Verify camera calibration parameters
3. Ensure all dependencies are installed
4. Test with different camera sources

---

**Last Updated**: December 2025
**Version**: 1.0 with Battery-Aware Features
