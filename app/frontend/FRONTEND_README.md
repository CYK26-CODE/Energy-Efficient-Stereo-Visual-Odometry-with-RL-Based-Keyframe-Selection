# 🎨 DQN SLAM Training Dashboard - Frontend Documentation

Professional CustomTkinter UI for real-time DQN training, parameter tuning, and performance monitoring.

## 📋 Overview

The frontend system provides a complete interface for:
- **Real-time training control** (start/pause/stop/resume)
- **Model parameter configuration** (learning rate, gamma, epsilon, batch size)
- **Reward weight optimization** (with presets and advanced configurator)
- **Battery degradation thresholds** (4-level configuration with presets)
- **Live performance monitoring** (reward graphs, loss curves, metrics)
- **Model management** (save/load trained agents)

## 🏗️ Architecture

### Core Components

```
frontend/
├── main_dashboard.py              # Main application window
├── backend_interface.py            # Backend communication layer
├── reward_configurator.py          # Reward weight configuration panel
├── degradation_configurator.py    # Battery threshold configuration panel
├── metrics_visualizer.py          # Real-time monitoring charts
├── training_dashboard.py          # Legacy simple dashboard
└── README.md                       # This file
```

### Integration Flow

```
┌─────────────────────────────────┐
│   Advanced DQN Training         │
│   Dashboard (main_dashboard.py) │
└────────────┬────────────────────┘
             │
    ┌────────┴──────────┬───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌──────────┐  ┌──────────────────┐  ┌──────────────┐
│ Training │  │  Configuration   │  │  Visualization
│ Control  │  │    Panels        │  │    Modules
│          │  │                  │  │
│• Start   │  │• DQN Params      │  │• Real-time
│• Pause   │  │• Reward Weights  │  │  Graphs
│• Stop    │  │• Battery Config  │  │• Metrics
│• Save    │  │• Metrics Display │  │• Statistics
└────┬─────┘  └────┬─────────────┘  └──────┬───────┘
     │             │                       │
     └─────────────┴───────────────────────┘
                   │
                   ▼
         ┌──────────────────────┐
         │ BackendInterface     │
         │ (backend_interface   │
         │  .py)               │
         └──────────────────────┘
                   │
                   ▼
         ┌──────────────────────┐
         │   Training Backend   │
         │ (train_dqn.py +     │
         │  DQN Agent +        │
         │  Energy Model)      │
         └──────────────────────┘
```

## 🚀 Quick Start

### Installation

1. **Install Dependencies:**
```powershell
cd c:\Users\chaitanya\Downloads\redi
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install frontend requirements
pip install customtkinter pillow matplotlib
```

2. **Run Main Dashboard:**
```powershell
python frontend/main_dashboard.py
```

### First Time Setup

1. **Configure DQN Parameters** (⚙️ DQN PARAMS tab)
   - Adjust learning rate, gamma, epsilon
   - Set batch size and update frequency
   - Default values optimized for most use cases

2. **Set Reward Weights** (⚖️ REWARDS tab)
   - Choose preset: Conservative/Balanced/Aggressive
   - Or use Advanced Configurator for fine-tuning
   - w_b: Localization accuracy weighting
   - w_e: Energy consumption penalty
   - w_l: Tracking loss penalty
   - w_t: Per-step exploration cost

3. **Configure Battery Levels** (🔋 BATTERY tab)
   - Set thresholds for L0→L1, L1→L2, L2→L3
   - Or use presets
   - Each level defines feature extraction strategy

4. **Start Training:**
   - Set episode count
   - Choose battery profile
   - Click "▶ START"

## 📊 Features

### 1. Training Control Panel

**Episodes Configuration:**
- Input desired number of episodes (default: 500)
- Select battery profile: constant, declining, variable
- Choose computing device: CPU or CUDA GPU

**Training Buttons:**
- ▶ **START** - Begin training from scratch
- ⏸ **PAUSE** - Suspend training (resume later)
- ⏹ **STOP** - End training session
- 💾 **SAVE** - Save trained model checkpoint
- 📂 **LOAD** - Load previously trained model
- 📊 **EXPORT** - Export metrics as JSON/CSV

**Progress Tracking:**
- Real-time progress bar
- Episode counter (current/total)
- Training status indicator (IDLE/TRAINING/PAUSED)

### 2. DQN Parameters Configuration

Adjust core DQN hyperparameters:

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| Learning Rate | 1e-5 to 1e-3 | 1e-4 | Adam optimizer learning rate |
| Gamma (γ) | 0.9 to 0.99 | 0.99 | Discount factor for future rewards |
| Epsilon Start (ε_start) | 0.1 to 1.0 | 0.3 | Initial exploration probability |
| Epsilon End (ε_end) | 0.01 to 0.2 | 0.05 | Final exploration probability |
| Batch Size | 16 to 256 | 64 | Training batch size |
| Target Update Freq | 100 to 5000 | 1000 | Steps between target network updates |

### 3. Reward Weight Configuration

**Built-in Presets:**

| Preset | w_b | w_e | w_l | w_t | Use Case |
|--------|-----|-----|-----|-----|----------|
| Conservative | 12.0 | 10.0 | 50.0 | 0.02 | Prioritize energy savings |
| Balanced | 8.0 | 6.0 | 40.0 | 0.01 | General purpose |
| Aggressive | 4.0 | 2.0 | 30.0 | 0.005 | Maximize localization quality |

**Manual Configuration:**
- Open "🎛️ ADVANCED CONFIGURATOR" button
- Use sliders to adjust weights
- Real-time visualization shows weight composition
- Save custom preset for later use

**Reward Components:**
```
Total Reward = 
  + w_b × localization_quality
  - w_e × (battery_weighted_energy_cost)
  - w_l × (tracking_loss_penalty)
  - w_t × (per_step_penalty)
```

### 4. Battery Degradation Configuration

**4 Degradation Levels:**

```
Level 0 (≥60% battery)  - FULL PERFORMANCE
├─ Feature Type: SIFT (high quality)
├─ Descriptor Retention: 100%
└─ Keyframe Frequency: Frequent

Level 1 (≥40% battery)  - BALANCED
├─ Feature Type: SIFT (selective)
├─ Descriptor Retention: 80%
└─ Keyframe Frequency: Moderate

Level 2 (≥20% battery)  - DEGRADED
├─ Feature Type: ORB (faster)
├─ Descriptor Retention: 50%
└─ Keyframe Frequency: Rare

Level 3 (<20% battery)  - CRITICAL
├─ Feature Type: FAST (minimal)
├─ Descriptor Retention: 20%
└─ Keyframe Frequency: Critical
```

**Preset Thresholds:**

| Preset | T0 | T1 | T2 | Strategy |
|--------|----|----|----|---------  |
| Conservative | 70% | 50% | 25% | Maximize runtime |
| Balanced | 60% | 40% | 20% | Balanced degradation |
| Aggressive | 50% | 30% | 15% | Maintain quality longer |

### 5. Real-Time Metrics Display

**Open via: 📊 METRICS tab → 📊 OPEN METRICS MONITOR**

Live visualization showing:
- **Episode Rewards**: Reward curve over training
- **Training Loss**: Loss convergence tracking
- **Uncertainty**: Localization uncertainty trends
- **Action Distribution**: SKIP vs SAVE vs LIGHT-SAVE ratio

**Export Options:**
- JSON format (structured data)
- CSV format (for Excel/analysis)
- Includes all episode metrics and summaries

### 6. Statistics Panel

Real-time statistics updated during training:

- **Episodes**: Total episodes completed
- **Avg Reward**: Mean reward across recent episodes
- **Avg Loss**: Mean training loss
- **Success Rate**: Percentage of successful episodes
- **Avg Uncertainty**: Mean localization uncertainty
- **Total Keyframes**: Cumulative keyframes extracted
- **Battery Level**: Current simulated battery %
- **Epsilon**: Current exploration probability

## 🔧 Configuration Files

### Automatic Configuration

Configurations are saved to `training_config.json`:

```json
{
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
```

### Model Checkpoints

Trained models saved as:
- Format: PyTorch `.pth` files
- Location: Backend folder
- Naming: `dqn_keyframe_model_YYYYMMDD_HHMMSS.pth`

## 🎯 Usage Workflow

### Training a Model

1. **Configure Parameters:**
   ```
   ⚙️ DQN PARAMS → Adjust as needed
   ⚖️ REWARDS → Choose preset or customize
   🔋 BATTERY → Set degradation thresholds
   ```

2. **Set Episodes:**
   - Enter desired episode count (recommend 500-1000)
   - Choose battery profile (declining recommended)

3. **Start Training:**
   - Click "▶ START"
   - Status changes to "TRAINING" (green dot)
   - Progress bar fills as episodes complete
   - Statistics update in real-time

4. **Monitor Progress:**
   - View stats panel on right
   - Open "📊 METRICS MONITOR" for detailed graphs
   - Watch loss curve decrease

5. **Save Model:**
   - Click "💾 SAVE" to checkpoint model
   - Export metrics for analysis

### Resuming Training

1. Click "📂 LOAD" to load previous model
2. Adjust parameters if desired
3. Set new episode count
4. Click "▶ START" to continue

### Parameter Tuning

**For Faster Training:**
- Increase batch size (64 → 128)
- Decrease epsilon decay slope
- Use Conservative reward preset

**For Better Quality:**
- Decrease learning rate (1e-4 → 1e-5)
- Increase episodes (500 → 2000)
- Use Aggressive reward preset

**For Battery-Aware Training:**
- Set battery_profile to "declining"
- Adjust w_e (energy weight) higher
- Use Conservative battery thresholds

## 📈 Performance Monitoring

### Understanding Metrics

| Metric | Interpretation | Target |
|--------|----------------|--------|
| Reward | Agent performance score | Increasing trend |
| Loss | Training error | Decreasing |
| Uncertainty | Localization confidence | < 0.3 (low is good) |
| Success Rate | % successful episodes | > 80% |
| Action Distribution | Skip/Save/Light ratio | Balanced mix |

### Reading the Loss Curve

```
Good Training:          Bad Training:
     │                      │ ╱╲
Loss │╲                  Loss │╱╲╱╲
     │ ╲___                  │    ╲___
     │     └──              │
     └──────────            └──────────
     Episodes              Episodes
```

The loss should smoothly decrease and plateau.

## 🛠️ Troubleshooting

### Dashboard Won't Start

```powershell
# Ensure dependencies installed
pip install customtkinter pillow matplotlib --upgrade

# Check Python version (3.8+ required)
python --version
```

### Training Not Starting

1. Check episode count is valid (> 0)
2. Verify backend files exist in `../backend/`
3. Check console for error messages
4. Ensure GPU available if CUDA selected

### Metrics Not Updating

1. Open metrics window after training starts
2. Wait for episode to complete
3. Check if training is actually running (status indicator)
4. Try pausing and resuming training

### Model Save/Load Errors

1. Ensure write permissions in backend folder
2. Check disk space available
3. Verify model file path is correct
4. Try with different filename

## 📚 Module Reference

### backend_interface.py

```python
BackendInterface()
  ├─ start_training(episodes, on_progress)
  ├─ pause_training()
  ├─ stop_training()
  ├─ save_model(filepath)
  ├─ load_model(filepath)
  ├─ export_metrics(filepath, format)
  ├─ update_config(config)
  ├─ update_reward_weights(weights)
  └─ update_battery_thresholds(thresholds)
```

### reward_configurator.py

```python
RewardConfigurator(parent, on_save, initial_weights)
  ├─ Interactive slider configuration
  ├─ Preset shortcuts
  └─ Real-time weight visualization
```

### degradation_configurator.py

```python
BatteryDegradationConfigurator(parent, on_save, initial_thresholds)
  ├─ 4 threshold sliders
  ├─ Level configuration display
  └─ Preset management
```

### metrics_visualizer.py

```python
RealtimeMetricsDisplay(parent)
  ├─ 4-subplot matplotlib figure
  ├─ add_episode_data(reward, loss, uncertainty, actions)
  └─ export methods
```

## 🎨 UI Customization

### Changing Colors

Edit `main_dashboard.py`:
```python
# Change primary color
ctk.set_default_color_theme("green")  # green/blue/red

# Edit specific widget colors
ctk.CTkButton(fg_color="#00ff00")  # Hex color
```

### Adjusting Layout

Modify geometry in `__init__`:
```python
self.geometry("1800x1000")  # Width x Height
```

### Scaling Text

Adjust fonts:
```python
font=("Roboto", 14, "bold")  # Size can be changed
```

## 🔌 Integration with Backend

The frontend communicates with backend via `BackendInterface`:

```python
# Creating interface
backend = BackendInterface()

# Registering callbacks
backend.on_episode_complete = my_callback

# Starting training
backend.start_training(500, on_progress=progress_callback)

# Accessing data
metrics = backend.get_latest_metrics()
summary = backend.get_metrics_summary()
```

## 📝 Advanced Topics

### Custom Reward Functions

Modify `energy_battery_model.py` in backend, then reload in UI.

### Real Hardware Integration

Integrate with actual SLAM system by modifying `SLAMSimulator` in `train_dqn.py`.

### Extended Metrics

Add new metrics to `TrainingLogger` in `monitoring_logging.py`.

## 📞 Support

For issues or questions:
1. Check error output in console
2. Verify all files are present
3. Ensure dependencies are latest version
4. Check that backend module files exist

## 📄 License

Part of DQN SLAM Intelligent Training System

---

**Last Updated:** 2024
**Version:** 1.0
**Status:** Production Ready ✅
