"""
Optimization result model.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
import json


@dataclass
class OptimizationMetrics:
    """Metrics from optimization result."""
    cost: float  # Total cost in currency units
    dissatisfaction: float  # Total dissatisfaction score
    peak_power: float  # Peak power in kW
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'cost': round(self.cost, 2),
            'dissatisfaction': round(self.dissatisfaction, 4),
            'peak_power': round(self.peak_power, 2)
        }


@dataclass
class OptimizationResult:
    """
    Complete optimization result.
    
    Attributes:
        metrics: Optimization metrics
        charging_schedule: Power schedule matrix (vehicles x hours)
        n_vehicles: Number of vehicles
        n_hours: Time horizon in hours
        solutions_found: Number of solutions in Pareto front
        execution_time: Optimization duration in seconds
        converged: Whether algorithm converged
        metadata: Additional information
    """
    metrics: OptimizationMetrics
    charging_schedule: np.ndarray
    n_vehicles: int
    n_hours: int
    solutions_found: int
    execution_time: float
    converged: bool = True
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    pareto_front: Optional[np.ndarray] = None  # All Pareto solutions (N x 3: cost, dissatisfaction, peak)
    performance_metrics: Optional[Dict] = None  # Global metrics (Hypervolume, Spacing, etc.)
    
    def get_vehicle_schedule(self, vehicle_idx: int) -> np.ndarray:
        """
        Get charging schedule for a specific vehicle.
        
        Args:
            vehicle_idx: Vehicle index
            
        Returns:
            Power schedule for vehicle (hourly)
        """
        if vehicle_idx >= self.n_vehicles:
            raise ValueError(f"Vehicle index {vehicle_idx} out of range")
        return self.charging_schedule[vehicle_idx, :]
    
    def get_hourly_total(self) -> np.ndarray:
        """
        Get total power consumption per hour.
        
        Returns:
            Array of hourly totals
        """
        return np.sum(self.charging_schedule, axis=0)
    
    def get_energy_per_vehicle(self) -> np.ndarray:
        """
        Calculate total energy delivered to each vehicle.
        
        Returns:
            Array of energy per vehicle in kWh
        """
        return np.sum(self.charging_schedule, axis=1)
    
    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            'metrics': self.metrics.to_dict(),
            'n_vehicles': self.n_vehicles,
            'n_hours': self.n_hours,
            'solutions_found': self.solutions_found,
            'execution_time': round(self.execution_time, 2),
            'converged': self.converged,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'performance_metrics': self.performance_metrics,
            'summary': {
                'total_energy': float(np.sum(self.charging_schedule)),
                'avg_power_per_vehicle': float(np.mean(self.get_energy_per_vehicle())),
                'peak_hour': int(np.argmax(self.get_hourly_total()))
            }
        }
    
    def to_json(self, filepath: str):
        """Save result to JSON file."""
        data = self.to_dict()
        # Add schedule as list
        data['charging_schedule'] = self.charging_schedule.tolist()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_schedule_csv(self, filepath: str):
        """Save charging schedule to CSV."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            header = ['Vehicle'] + [f'Hour_{h:02d}' for h in range(self.n_hours)]
            writer.writerow(header)
            
            # Data
            for i in range(self.n_vehicles):
                row = [f'V{i+1:02d}'] + [f'{p:.2f}' for p in self.charging_schedule[i, :]]
                writer.writerow(row)
    
    def save_pareto_front_csv(self, filepath: str):
        """Save Pareto front objectives to CSV."""
        if self.pareto_front is None:
            return
        
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['solution_id', 'cost', 'dissatisfaction', 'peak_power'])
            
            # Data - each solution
            for i, solution in enumerate(self.pareto_front):
                row = [i, f'{solution[0]:.2f}', f'{solution[1]:.4f}', f'{solution[2]:.2f}']
                writer.writerow(row)
