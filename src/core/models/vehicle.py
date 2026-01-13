"""
Vehicle domain model representing an electric vehicle in the charging system.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class Vehicle:
    """
    Represents an electric vehicle with charging requirements.
    
    Attributes:
        id: Unique identifier for the vehicle
        battery_capacity: Total battery capacity in kWh
        soc_initial: Initial State of Charge (0.0-1.0)
        soc_target: Target State of Charge for departure (0.0-1.0)
        arrival_time: Hour of arrival (0-23)
        departure_time: Hour of departure (0-23)
        user_id: Optional user identifier
        charging_power_min: Minimum charging power (negative for V2G) in kW
        charging_power_max: Maximum charging power in kW
    """
    battery_capacity: float
    soc_initial: float
    soc_target: float
    arrival_time: int
    departure_time: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    charging_power_min: float = -6.0  # V2G capability
    charging_power_max: float = 30.0
    
    def __post_init__(self):
        """Validate vehicle parameters."""
        self._validate()
    
    def _validate(self):
        """Validate all vehicle parameters."""
        if not 0 <= self.soc_initial <= 1.0:
            raise ValueError(f"soc_initial must be between 0 and 1, got {self.soc_initial}")
        
        if not 0 <= self.soc_target <= 1.0:
            raise ValueError(f"soc_target must be between 0 and 1, got {self.soc_target}")
        
        if not 0 <= self.arrival_time < 24:
            raise ValueError(f"arrival_time must be between 0 and 23, got {self.arrival_time}")
        
        if not 0 <= self.departure_time < 24:
            raise ValueError(f"departure_time must be between 0 and 23, got {self.departure_time}")
        
        if self.battery_capacity <= 0:
            raise ValueError(f"battery_capacity must be positive, got {self.battery_capacity}")
    
    def available_at(self, hour: int) -> bool:
        """
        Check if vehicle is available at a given hour.
        
        Args:
            hour: Hour to check (0-23)
            
        Returns:
            True if vehicle is present at this hour
        """
        if self.departure_time > self.arrival_time:
            # Same day
            return self.arrival_time <= hour < self.departure_time
        else:
            # Overnight stay
            return hour >= self.arrival_time or hour < self.departure_time
    
    def energy_needed(self) -> float:
        """
        Calculate total energy needed to reach target SoC.
        
        Returns:
            Energy in kWh
        """
        return (self.soc_target - self.soc_initial) * self.battery_capacity
    
    def hours_available(self) -> int:
        """
        Calculate number of hours vehicle is available.
        
        Returns:
            Number of hours
        """
        if self.departure_time > self.arrival_time:
            return self.departure_time - self.arrival_time
        else:
            return (24 - self.arrival_time) + self.departure_time
    
    def minimum_charging_power(self) -> float:
        """
        Calculate minimum average charging power needed to meet target.
        
        Returns:
            Power in kW
        """
        hours = self.hours_available()
        if hours == 0:
            return float('inf')
        return self.energy_needed() / hours
    
    def to_dict(self) -> dict:
        """Convert vehicle to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'battery_capacity': self.battery_capacity,
            'soc_initial': self.soc_initial,
            'soc_target': self.soc_target,
            'arrival_time': self.arrival_time,
            'departure_time': self.departure_time,
            'charging_power_min': self.charging_power_min,
            'charging_power_max': self.charging_power_max,
            'energy_needed': self.energy_needed(),
            'hours_available': self.hours_available()
        }
