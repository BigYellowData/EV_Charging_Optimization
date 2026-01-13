"""
Synthetic data generator implementing ISyntheticDataSource.
"""
import numpy as np
from typing import Optional

from ...core.interfaces.data_source import ISyntheticDataSource
from ...core.entities.scenario import Scenario
from ...core.models.vehicle import Vehicle
from ...config.logging_config import get_logger
from ...config.settings import settings

logger = get_logger(__name__)


class SyntheticDataGenerator(ISyntheticDataSource):
    """Generates synthetic charging scenarios for testing."""
    
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
            site_max_power: Maximum site power
            seed: Random seed for reproducibility
            
        Returns:
            Generated scenario
        """
        if seed is not None:
            np.random.seed(seed)
        
        logger.info(f"Generating synthetic scenario: {n_vehicles} vehicles, {time_horizon}h horizon")
        
        # Generate vehicles
        vehicles = []
        for i in range(n_vehicles):
            vehicle = self._generate_vehicle(i)
            vehicles.append(vehicle)
        
        # Generate price profile
        price_profile = self._generate_price_profile(time_horizon)
        
        scenario = Scenario(
            vehicles=vehicles,
            price_profile=price_profile,
            site_max_power=site_max_power,
            time_horizon=time_horizon,
            name=f"synthetic_{n_vehicles}v"
        )
        
        logger.info(f"Generated scenario: {scenario.total_energy_demand():.1f} kWh total demand")
        return scenario
    
    def _generate_vehicle(self, idx: int) -> Vehicle:
        """Generate a single synthetic vehicle."""
        # Typical workplace charging patterns
        arrival = np.random.randint(6, 10)  # Arrive 6am-10am
        departure = np.random.randint(17, 22)  # Leave 5pm-10pm
        
        # Battery state
        soc_initial = np.random.uniform(0.1, 0.4)  # Low battery
        soc_target = np.random.uniform(0.8, 1.0)  # Want full charge
        
        return Vehicle(
            battery_capacity=settings.battery_capacity,
            soc_initial=soc_initial,
            soc_target=soc_target,
            arrival_time=arrival,
            departure_time=departure,
            user_id=f"synthetic_{idx:03d}",
            charging_power_min=settings.charging_power_min,
            charging_power_max=settings.charging_power_max
        )
    
    def _generate_price_profile(self, time_horizon: int) -> np.ndarray:
        """Generate realistic price profile."""
        hours = np.arange(time_horizon)
        
        # Sinusoidal pattern: expensive during day, cheap at night
        base_price = 0.15
        amplitude = 0.10
        prices = base_price + amplitude * np.sin((hours - 6) * np.pi / 12) ** 2
        
        return prices
