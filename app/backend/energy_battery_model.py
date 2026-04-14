#!/usr/bin/env python3
"""
Energy and Battery Modeling
Tracks energy consumption and battery state for reward shaping
"""

import numpy as np
import psutil
import time
from typing import Dict, Tuple
from collections import deque


class EnergyModel:
    """
    Models energy consumption for SLAM operations
    Provides normalized energy costs for actions
    """
    
    # Energy costs (normalized, relative to worst-case)
    ENERGY_COSTS = {
        'skip_frame': 0.02,                # Minimal: just tracking
        'save_light': 0.2,                 # Light: pose + reduced descriptors
        'save_normal': 0.6,                # Normal: full descriptor set
        'save_high': 1.0,                  # High: full + extra processing
        'bundle_adjustment': 0.3,          # Bundle adjustment optimization
        'loop_closure_check': 0.15,        # Loop closure detection
        'map_transmission': 0.4            # Transmit map data
    }
    
    def __init__(self, reference_energy_mj: float = 100.0):
        """
        Initialize energy model
        
        Args:
            reference_energy_mj: Reference energy in mJ for normalization
        """
        self.reference_energy = reference_energy_mj
        self.accumulated_energy = 0.0
        self.energy_history = deque(maxlen=1000)
    
    def get_action_cost(self, action: int) -> float:
        """
        Get normalized energy cost for action
        
        Args:
            action: 0=skip, 1=save_normal, 2=save_light
            
        Returns:
            Normalized cost [0, 1]
        """
        if action == 0:  # SKIP
            return self.ENERGY_COSTS['skip_frame']
        elif action == 1:  # SAVE_NORMAL
            return self.ENERGY_COSTS['save_normal']
        elif action == 2:  # SAVE_LIGHT
            return self.ENERGY_COSTS['save_light']
        else:
            return 0.0
    
    def record_energy(self, energy_mj: float):
        """Record energy measurement"""
        self.accumulated_energy += energy_mj
        self.energy_history.append(energy_mj)
    
    def get_recent_energy_rate(self, window_size: int = 10) -> float:
        """
        Get average energy consumption rate
        
        Returns:
            Energy per frame (normalized)
        """
        if len(self.energy_history) < window_size:
            return 0.0
        
        recent = list(self.energy_history)[-window_size:]
        avg_energy = np.mean(recent)
        return min(avg_energy / self.reference_energy, 1.0)
    
    def estimate_remaining_runtime(self, battery_pct: float, avg_power_w: float) -> float:
        """
        Estimate remaining runtime
        
        Args:
            battery_pct: Battery percentage [0, 100]
            avg_power_w: Average power consumption in watts
            
        Returns:
            Estimated runtime in seconds
        """
        if avg_power_w < 0.001:
            return float('inf')
        
        # Assume 100Wh battery (typical laptop)
        battery_capacity_wh = 100.0
        available_wh = (battery_pct / 100.0) * battery_capacity_wh
        
        runtime_hours = available_wh / avg_power_w
        return runtime_hours * 3600.0  # Convert to seconds


class BatteryMonitor:
    """
    Monitor and track battery state
    Provides normalized battery percentage and degradation levels
    """
    
    # Degradation thresholds
    BATTERY_FULL = 60.0           # >= 60%: Level 0 (full)
    BATTERY_MILD = 40.0           # 40-60%: Level 1 (mild)
    BATTERY_MODERATE = 20.0       # 20-40%: Level 2 (moderate)
    BATTERY_AGGRESSIVE = 0.0      # < 20%: Level 3 (aggressive)
    
    def __init__(self, update_interval: float = 5.0):
        """
        Initialize battery monitor
        
        Args:
            update_interval: Seconds between battery updates
        """
        self.current_battery = 100.0
        self.battery_history = deque(maxlen=1000)
        self.last_update = time.time()
        self.update_interval = update_interval
        self.last_battery_drop = 0.0
        self.battery_drop_rate = 0.0  # %/second
    
    def update(self) -> float:
        """
        Update battery reading
        
        Returns:
            Current battery percentage [0, 100]
        """
        current_time = time.time()
        
        if current_time - self.last_update >= self.update_interval:
            try:
                battery = psutil.sensors_battery()
                if battery is not None:
                    prev_battery = self.current_battery
                    self.current_battery = battery.percent
                    
                    # Calculate drop rate
                    time_delta = current_time - self.last_update
                    battery_delta = prev_battery - self.current_battery
                    
                    if time_delta > 0:
                        self.battery_drop_rate = battery_delta / time_delta  # %/second
                    
                    self.battery_history.append(self.current_battery)
                    self.last_update = current_time
            except:
                pass
        
        return self.current_battery
    
    def get_normalized_battery(self) -> float:
        """Get battery percentage normalized to [0, 1]"""
        return self.current_battery / 100.0
    
    def get_degradation_level(self) -> int:
        """
        Get degradation level based on battery
        
        Returns:
            0=full, 1=mild, 2=moderate, 3=aggressive
        """
        if self.current_battery >= self.BATTERY_FULL:
            return 0
        elif self.current_battery >= self.BATTERY_MILD:
            return 1
        elif self.current_battery >= self.BATTERY_MODERATE:
            return 2
        else:
            return 3
    
    def get_energy_weight_multiplier(self, k_batt: float = 1.5) -> float:
        """
        Get battery-aware energy weight multiplier
        Energy cost gets multiplied by this factor
        
        When battery low, energy costs more (encourage skipping)
        
        Args:
            k_batt: Scaling factor (1.5 = energy cost doubles at 0% battery)
            
        Returns:
            Multiplier [1.0, 1+k_batt]
        """
        norm_battery = self.get_normalized_battery()
        return 1.0 + k_batt * (1.0 - norm_battery)
    
    def get_battery_status(self) -> Dict:
        """Get detailed battery status"""
        return {
            'current_pct': self.current_battery,
            'normalized': self.get_normalized_battery(),
            'degradation_level': self.get_degradation_level(),
            'drop_rate_pct_per_sec': self.battery_drop_rate,
            'estimated_runtime_sec': self._estimate_runtime(),
            'energy_weight_mult': self.get_energy_weight_multiplier()
        }
    
    def _estimate_runtime(self) -> float:
        """Estimate remaining runtime based on drop rate"""
        if self.battery_drop_rate <= 0.0:
            return float('inf')
        
        remaining_pct = self.current_battery
        runtime_sec = remaining_pct / self.battery_drop_rate
        return max(0, runtime_sec)
    
    def get_battery_mode(self) -> str:
        """
        Get human-readable battery mode
        
        Returns:
            'critical', 'low', 'moderate', or 'good'
        """
        level = self.get_degradation_level()
        if level == 3:
            return 'critical'
        elif level == 2:
            return 'low'
        elif level == 1:
            return 'moderate'
        else:
            return 'good'


class EnergyAwareRewardCalculator:
    """
    Calculates reward for DQN training
    Combines localization benefit with energy cost
    """
    
    # Reward weights
    W_BENEFIT = 8.0          # Localization improvement weight
    W_ENERGY = 6.0           # Energy cost weight
    W_TRACKING_LOSS = 40.0   # Tracking loss penalty
    W_STEP = 0.01            # Per-step penalty (discourage dithering)
    
    # Clamp values for stability
    MAX_GAIN = 0.2
    MAX_LOSS = 0.2
    
    # Optional bonuses/penalties
    BONUS_SKIP = 2.0         # Bonus for successful skip
    PENALTY_WASTE = 3.0      # Penalty for wasted save
    
    def __init__(self, energy_model: EnergyModel, battery_monitor: BatteryMonitor):
        """
        Initialize reward calculator
        
        Args:
            energy_model: EnergyModel instance
            battery_monitor: BatteryMonitor instance
        """
        self.energy_model = energy_model
        self.battery_monitor = battery_monitor
    
    def compute_reward(self, 
                       action: int,
                       prev_uncertainty: float,
                       curr_uncertainty: float,
                       tracking_ok: bool,
                       keyframe_was_useful: bool = True,
                       battery_aware: bool = True) -> float:
        """
        Compute dense reward for DQN
        
        Args:
            action: 0=skip, 1=save_normal, 2=save_light
            prev_uncertainty: Previous uncertainty [0, 1]
            curr_uncertainty: Current uncertainty [0, 1]
            tracking_ok: Whether tracking remains good
            keyframe_was_useful: Whether saved keyframe reduced uncertainty
            battery_aware: Whether to apply battery-aware shaping
            
        Returns:
            Reward scalar
        """
        reward = 0.0
        
        # 1. Localization improvement/degradation
        delta_uncertainty = np.clip(prev_uncertainty - curr_uncertainty, 
                                    -self.MAX_LOSS, self.MAX_GAIN)
        localization_reward = delta_uncertainty * self.W_BENEFIT
        
        # 2. Energy cost (action-dependent)
        energy_cost = self.energy_model.get_action_cost(action)
        
        # Apply battery-aware weighting
        if battery_aware:
            energy_weight = self.W_ENERGY * self.battery_monitor.get_energy_weight_multiplier()
        else:
            energy_weight = self.W_ENERGY
        
        energy_penalty = -energy_weight * energy_cost
        
        # 3. Tracking loss penalty
        if not tracking_ok:
            tracking_penalty = -self.W_TRACKING_LOSS
        else:
            tracking_penalty = 0.0
        
        # 4. Per-step penalty (tiny, to discourage dithering)
        step_penalty = -self.W_STEP
        
        # 5. Optional bonuses/penalties
        bonus = 0.0
        if action == 0 and tracking_ok and delta_uncertainty > -0.05:  # Successful skip
            bonus += self.BONUS_SKIP
        
        if action > 0 and not keyframe_was_useful:  # Wasted save
            bonus -= self.PENALTY_WASTE
        
        # Total reward
        reward = localization_reward + energy_penalty + tracking_penalty + step_penalty + bonus
        
        # Clamp to reasonable range
        reward = np.clip(reward, -50.0, 50.0)
        
        return reward
    
    def compute_batch_reward(self,
                            actions: np.ndarray,
                            prev_uncertainties: np.ndarray,
                            curr_uncertainties: np.ndarray,
                            tracking_flags: np.ndarray) -> np.ndarray:
        """
        Compute rewards for batch of transitions
        
        Args:
            actions: [batch_size]
            prev_uncertainties: [batch_size]
            curr_uncertainties: [batch_size]
            tracking_flags: [batch_size]
            
        Returns:
            rewards: [batch_size]
        """
        batch_size = len(actions)
        rewards = np.zeros(batch_size)
        
        for i in range(batch_size):
            rewards[i] = self.compute_reward(
                actions[i],
                prev_uncertainties[i],
                curr_uncertainties[i],
                tracking_flags[i]
            )
        
        return rewards
