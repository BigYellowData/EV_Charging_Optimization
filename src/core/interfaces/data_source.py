"""
Data source interfaces for abstracting data providers.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from ..models.charging_session import ChargingSession
from ..entities.scenario import Scenario


class IDataSource(ABC):
    """Interface for data sources providing charging scenarios."""
    
    @abstractmethod
    def fetch_sessions(
        self,
        start_date: date,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[ChargingSession]:
        """
        Fetch charging sessions from data source.
        
        Args:
            start_date: Start date for data retrieval
            end_date: Optional end date (defaults to start_date)
            limit: Maximum number of sessions to retrieve
            
        Returns:
            List of charging sessions
        """
        pass
    
    @abstractmethod
    def build_scenario(
        self,
        sessions: List[ChargingSession],
        site_max_power: float,
        time_horizon: int = 24
    ) -> Scenario:
        """
        Build optimization scenario from sessions.
        
        Args:
            sessions: List of charging sessions
            site_max_power: Maximum site power in kW
            time_horizon: Planning horizon in hours
            
        Returns:
            Complete optimization scenario
        """
        pass


class ISyntheticDataSource(ABC):
    """Interface for synthetic data generation."""
    
    @abstractmethod
    def generate_scenario(
        self,
        n_vehicles: int,
        time_horizon: int,
        site_max_power: float,
        seed: Optional[int] = None
    ) -> Scenario:
        """
        Generate synthetic charging scenario.
        
        Args:
            n_vehicles: Number of vehicles
            time_horizon: Planning horizon in hours
            site_max_power: Maximum site power in kW
            seed: Random seed for reproducibility
            
        Returns:
            Generated scenario
        """
        pass
