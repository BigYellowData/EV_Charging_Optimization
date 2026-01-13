"""
Scenario entity representing a complete charging optimization scenario.
"""
from dataclasses import dataclass, field
from typing import List
import numpy as np

from ..models.vehicle import Vehicle


@dataclass
class Scenario:
    """
    Complete charging scenario with vehicles, prices, and constraints.
    
    Attributes:
        vehicles: List of vehicles to charge
        price_profile: Hourly electricity prices
        site_max_power: Maximum site power capacity in kW
        time_horizon: Number of hours in the planning horizon
        name: Optional scenario name
    """
    vehicles: List[Vehicle]
    price_profile: np.ndarray
    site_max_power: float
    time_horizon: int = 24
    name: str = "default"
    
    def __post_init__(self):
        """Validate scenario."""
        if len(self.price_profile) != self.time_horizon:
            raise ValueError(
                f"Price profile length ({len(self.price_profile)}) "
                f"must match time horizon ({self.time_horizon})"
            )
        
        if self.site_max_power <= 0:
            raise ValueError(f"site_max_power must be positive, got {self.site_max_power}")
        
        if not self.vehicles:
            raise ValueError("Scenario must have at least one vehicle")
    
    def get_availability_mask(self) -> np.ndarray:
        """
        Create availability mask for all vehicles.
        
        Returns:
            Boolean matrix (n_vehicles x time_horizon)
        """
        mask = np.zeros((len(self.vehicles), self.time_horizon), dtype=bool)
        
        for i, vehicle in enumerate(self.vehicles):
            for hour in range(self.time_horizon):
                mask[i, hour] = vehicle.available_at(hour)
        
        return mask
    
    def get_initial_soc_vector(self) -> np.ndarray:
        """Get initial SoC for all vehicles."""
        return np.array([v.soc_initial for v in self.vehicles])
    
    def get_target_soc_vector(self) -> np.ndarray:
        """Get target SoC for all vehicles."""
        return np.array([v.soc_target for v in self.vehicles])
    
    def get_departure_times(self) -> np.ndarray:
        """Get departure times for all vehicles."""
        return np.array([v.departure_time for v in self.vehicles])
    
    def get_battery_capacities(self) -> np.ndarray:
        """Get battery capacities for all vehicles."""
        return np.array([v.battery_capacity for v in self.vehicles])
    
    def total_energy_demand(self) -> float:
        """Calculate total energy demand for all vehicles."""
        return sum(v.energy_needed() for v in self.vehicles)
    
    def is_feasible(self) -> bool:
        """
        Check if scenario is theoretically feasible.
        
        Returns:
            True if all vehicles can potentially be charged
        """
        for vehicle in self.vehicles:
            min_power = vehicle.minimum_charging_power()
            if min_power > vehicle.charging_power_max:
                return False
        return True
    
    def to_dict(self) -> dict:
        """Convert scenario to dictionary."""
        return {
            'name': self.name,
            'n_vehicles': len(self.vehicles),
            'time_horizon': self.time_horizon,
            'site_max_power': self.site_max_power,
            'total_energy_demand': self.total_energy_demand(),
            'feasible': self.is_feasible(),
            'vehicles': [v.to_dict() for v in self.vehicles],
            'price_profile': self.price_profile.tolist()
        }
