# SLAM + RL Training System

A stereo SLAM and reinforcement learning project with:
- Real-time stereo processing (OpenCV)
- RL-driven keyframe strategy
- Training dashboard (CustomTkinter)
- PyInstaller packaging for standalone executables

This README is the single source of truth for setup, architecture, workflows, and build guidance.

## 1. Project Overview

The repository combines three major layers:
- Runtime SLAM layer: stereo camera ingest, feature extraction, odometry, mapping
- RL/training layer: DQN and energy-aware reward shaping
- Frontend layer: dashboard controls, configurators, and live metrics

Primary code folders:
- `app/runtime/`: packaged runtime modules used by build specs
- `app/backend/`: training and policy modules
- `app/frontend/`: dashboard and UI integration

## 2. Quick Start

### 2.1 Prerequisites
- Python 3.8+
- Windows recommended (project includes `.bat` build scripts)
- 4 GB RAM minimum, 8 GB recommended

### 2.2 Install Dependencies

```powershell
cd c:\Users\chaitanya\Downloads\redi
pip install -r app/runtime/requirements.txt
```

Optional for packaging:

```powershell
pip install -r requirements_build.txt
```

### 2.3 Launch Main Dashboard

```powershell
python app/frontend/launch.py
```

Alternative direct launch:

```powershell
python app/frontend/main_dashboard.py
```

## 3. Core Run Modes

### 3.1 Full Dashboard + Training
- Entry: `app/frontend/launch.py`
- Use for parameter tuning, training control, metrics visualization

### 3.2 Integrated SLAM + RL (Direct launcher)
- Entry: `tools/launch_integrated_slam_rl.py`
- Use for integrated SLAM runtime with RL keyframe behavior

### 3.3 RL Agent Trainer (CLI style)
- Entry: `tools/launch_rl_trainer.py`
- Use for standalone RL training runs

## 4. Build Executables

### 4.1 Recommended Build

```powershell
.\build_all_exe.bat
```

Creates standalone executables in `dist/`.

### 4.2 Build Individual Targets

```powershell
pyinstaller --clean complete_slam.spec
pyinstaller --clean basic_slam.spec
pyinstaller --clean rl_trainer.spec
```

### 4.3 Build Artifacts
- Temporary build data: `build/`
- Final executables: `dist/`

## 5. Architecture

## 5.1 High-Level Data Flow

```text
User UI (app/frontend/main_dashboard.py)
    -> backend_interface.py
    -> train_dqn.py / runtime SLAM modules
    -> dqn_agent.py + energy_battery_model.py + degradation_policy.py
    -> monitoring_logging.py
    -> metrics back to UI visualizers
```

### 5.2 Major Components

Frontend:
- `app/frontend/main_dashboard.py`: primary dashboard
- `app/frontend/backend_interface.py`: frontend-backend bridge
- `app/frontend/reward_configurator.py`: reward tuning UI
- `app/frontend/degradation_configurator.py`: battery/degradation UI
- `app/frontend/metrics_visualizer.py`: charts and metric plots

Backend:
- `app/backend/train_dqn.py`: training orchestration
- `app/backend/dqn_agent.py`: DQN model and action policy
- `app/backend/energy_battery_model.py`: energy/reward modeling
- `app/backend/degradation_policy.py`: quality degradation policy
- `app/backend/monitoring_logging.py`: logs, exports, summaries

Runtime SLAM (`app/runtime/`):
- `app/runtime/stereo_slam.py`
- `app/runtime/stereo_vision.py`
- `app/runtime/visual_odometry.py`
- `app/runtime/camera_stream_handler.py`
- `app/runtime/integrated_slam.py`
- `app/runtime/integrated_slam_rl.py`

## 6. Configuration

Common configuration/data files:
- `app/runtime/camera_calibration.json`: calibration and camera parameters
- `training_config.json`: generated or updated by dashboard/training workflows
- `camera_config.json`: camera IP settings persisted by launchers

## 7. Testing and Validation

Current test scripts:
- `tests/test_slam_integration.py`
- `tests/test_integration.py`

Run examples:

```powershell
python tests/test_slam_integration.py
python tests/test_integration.py
```

## 8. Troubleshooting

### 8.1 Import Errors
- Ensure you run commands from repo root
- Ensure dependencies are installed from `app/runtime/requirements.txt`

### 8.2 Camera Stream Issues
- Verify camera URL is reachable in browser (`http://<ip>/stream`)
- Ensure host and cameras are on the same network
- Use synthetic mode for offline testing where available

### 8.3 Build Failures

```powershell
pip uninstall pyinstaller
pip install pyinstaller
pyinstaller --clean complete_slam.spec
```

## 9. Repository Conventions

This repository is currently being cleaned and restructured in batches.
- Documentation is consolidated into this `README.md`
- Duplicate/legacy docs are being removed
- Folder refactor is performed incrementally with verification after each batch

## 10. Related Technical References

Keep these code-focused references for deeper understanding:
- `app/backend/BACKEND_DOCUMENTATION.py`
- `app/backend/RL_KEYFRAME_SELECTION.md`
- `RL_AGENT_EXPLANATION.md`
- `app/frontend/FRONTEND_README.md`

## 11. Current Status

- Runtime, training, and UI paths are available
- Build specs are present and tied to existing folder structure
- Cleanup and structural refactor are in progress with safety-first migration
