# Energy-Efficient Stereo SLAM using Reinforcement Learning: A Research Overview

## Abstract
This project presents an integrated Stereo Simultaneous Localization and Mapping (SLAM) system designed for battery-constrained environments (e.g., drones, mobile robots). The core innovation lies in the application of Reinforcement Learning (RL) to dynamically manage keyframe selection strategies. By balancing localization accuracy with computational energy consumption, the system aims to extend operational lifespan without compromising navigation integrity.

## 1. Introduction
Traditional Visual SLAM systems are computationally intensive, often consuming significant power for continuous feature extraction, matching, and optimization (Bundle Adjustment). For autonomous mobile agents, this battery drain limits mission duration. This research proposes an "Energy-Aware" SLAM architecture that utilizes a Q-Learning agent to intelligently decide when to process frames as high-fidelity keyframes versus when to skip or reduce processing, based on real-time battery status and localization uncertainty.

## 2. Methodology

### 2.1 Stereo SLAM Baseline
The underlying visual odometry engine is built upon standard sparse stereo techniques:
- **Feature Detection**: SIFT (Scale-Invariant Feature Transform) is used for robust feature matching.
- **Stereo Matching**: Disparity maps are generated to calculate depth ($z = \frac{f \cdot B}{d}$).
- **Motion Estimation**: 3D-to-2D projection and PnP (Perspective-n-Point) resolution.
- **Optimization**: Global Bundle Adjustment (BA) refines camera poses and 3D landmarks.

### 2.2 Adaptive Keyframe Selection (The Novelty)
Standard SLAM systems create keyframes based purely on geometric thresholds (distance/rotation). This system introduces two adaptive layers:

#### A. Heuristic Battery Management
A rule-based degradation policy adjusts frame processing rates based on raw battery levels:
- **Good (>50%)**: Process all frames.
- **Moderate (<50%)**: Skip every other frame.
- **Low (<15%)**: Aggressive skipping (1 in 4).
- **Critical (<5%)**: Keyframe-only processing.

#### B. Reinforcement Learning Agent (Q-Learning)
To surpass static heuristics, a tabular Q-Learning agent ($\pi^*$) governs the decision process.

*   **State Space ($S$)**: A tuple representing the agent's context.
    *   `Uncertainty`: Variance in localization estimation (Normalised $[0, 1]$).
    *   `Energy Need`: Inverse of battery level (Higher battery = low need).
    *   `Battery Mode`: Categorical $\{Critical, Low, Moderate, Good\}$.

*   **Action Space ($A$)**:
    *   $a_0$: **CREATE_KEYFRAME** (High compute, lowers uncertainty).
    *   $a_1$: **SKIP_FRAME** (Low compute, saves energy, risk of drift).

*   **Reward Function ($R$)**:
    The reward balances conflicting objectives:
    $$ R = \lambda_1 \cdot (\Delta \text{Uncertainty}) - \lambda_2 \cdot (\text{EnergyCost}) $$
    *   Creating a keyframe yields positive reward if it significantly reduces uncertainty, but incurs a penalty proportional to the current "Energy Need".
    *   Skipping yields a positive reward for saving energy, but a penalty if uncertainty becomes too high.

## 3. System Architecture

The system is modularized into Frontend and Backend components:

1.  **Frontend**:
    *   `camera_stream_handler.py`: Manages stereo inputs.
    *   `stereo_vision.py`: Computes disparity and depth maps.

2.  **Backend (Intelligence)**:
    *   `rl_keyframe_selector.py`: HOSTs the Q-Table and updates policies.
    *   `integrated_slam_rl.py`: The main loop integrating the RL agent with the SLAM pipeline.
    *   `energy_battery_model.py`: Simulates battery discharge curves to train the agent without physical hardware risks.

3.  **Analysis**:
    *   `monitoring_logging.py`: Record telemetry for post-hoc analysis.

## 4. Experimental Setup & Results

Experiments are conducted using pre-recorded datasets to ensure reproducibility. The system includes a `run_research_experiment.py` module to automate trials.

### Metrics Recorded
- **Trajectory Error**: Deviation from ground truth (or high-fidelity baseline).
- **Keyframe Count**: Total keyframes created (proxy for compute load).
- **Battery Life**: Simulated discharge percentage over fixed trajectory.
- **Processing Time**: Average milliseconds per frame.

### Preliminary Observations
*   **Baseline (Full Fidelity)**: High accuracy, fastest battery drain.
*   **RL-Policy**: Demonstrates ability to maintain tracking during "Moderate" battery levels by selectively creating keyframes only at visually complex turns or unstable tracking moments, effectively ignoring redundant straight-line segments.

## 5. Implementation Details
*   **Language**: Python 3.x
*   **Libraries**: OpenCV (Vision), NumPy (Math), Matplotlib (Visualization).
*   **Training**: The agent supports both offline training (simulation) and online adaptation.

## 6. Future Work
*   **Deep RL**: Replacing the tabular Q-learning with a Deep Q-Network (DQN) to handle continuous state spaces (e.g., raw pixel entropy).
*   **Loop Closure Optimization**: Extending the RL agent to decide when to perform expensive global optimization steps.

---
*Generated by GitHub Copilot regarding the "Integrated Stereo SLAM System" workspace.*
