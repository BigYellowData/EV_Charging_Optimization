"""
Charging session model representing real-world charging data.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ChargingSession:
    """
    Represents a real charging session from Caltech dataset.
    
    Attributes:
        session_id: Unique session identifier
        user_id: User identifier
        connection_time: When vehicle was plugged in
        disconnection_time: When vehicle was unplugged
        kwh_delivered: Total energy delivered in kWh
        site_name: Name of the charging site
    """
    session_id: str
    user_id: str
    connection_time: datetime
    disconnection_time: datetime
    kwh_delivered: float
    site_name: str
    
    def __post_init__(self):
        """Validate session data."""
        if self.disconnection_time <= self.connection_time:
            raise ValueError("Disconnection time must be after connection time")
        
        if self.kwh_delivered < 0:
            raise ValueError(f"kwh_delivered must be positive, got {self.kwh_delivered}")
    
    def duration_hours(self) -> float:
        """
        Calculate session duration in hours.
        
        Returns:
            Duration in hours
        """
        delta = self.disconnection_time - self.connection_time
        return delta.total_seconds() / 3600
    
    def average_power(self) -> float:
        """
        Calculate average charging power.
        
        Returns:
            Average power in kW
        """
        duration = self.duration_hours()
        if duration == 0:
            return 0.0
        return self.kwh_delivered / duration
    
    def arrival_hour(self) -> int:
        """Get arrival hour (0-23)."""
        return self.connection_time.hour
    
    def departure_hour(self) -> int:
        """Get departure hour (0-23)."""
        return self.disconnection_time.hour
    
    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'connection_time': self.connection_time.isoformat(),
            'disconnection_time': self.disconnection_time.isoformat(),
            'kwh_delivered': self.kwh_delivered,
            'site_name': self.site_name,
            'duration_hours': self.duration_hours(),
            'average_power': self.average_power(),
            'arrival_hour': self.arrival_hour(),
            'departure_hour': self.departure_hour()
        }
