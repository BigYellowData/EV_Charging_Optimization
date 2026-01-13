"""
Caltech ACN-Data repository implementation.
"""
import requests
from typing import List, Optional
from datetime import date, datetime
from pathlib import Path
import time

from ...core.models.charging_session import ChargingSession
from ...core.interfaces.data_source import IDataSource
from ...core.entities.scenario import Scenario
from ...core.models.vehicle import Vehicle
from ...core.exceptions import DataSourceError
from ...config.logging_config import get_logger
from ...config.settings import settings
import numpy as np

logger = get_logger(__name__)


class CaltechRepository(IDataSource):
    """Repository for Caltech ACN-Data API."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Caltech repository.
        
        Args:
            api_url: API base URL (defaults to settings)
            api_key: API key (defaults to settings)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.api_url = api_url or settings.caltech_api_url
        self.api_key = api_key or settings.get_api_key()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info(f"Initialized CaltechRepository (url={self.api_url})")
    
    def _make_request(self, url: str, params: dict) -> dict:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response
            
        Raises:
            DataSourceError: If request fails after retries
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"API request attempt {attempt + 1}/{self.max_retries}: {url}")
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise DataSourceError(f"API request failed after {self.max_retries} attempts: {e}")
    
    def fetch_sessions(
        self,
        start_date: date,
        end_date: Optional[date] = None,
        site: str = "caltech",
        limit: Optional[int] = None
    ) -> List[ChargingSession]:
        """
        Fetch charging sessions from Caltech API.
        
        Args:
            start_date: Start date
            end_date: End date (defaults to start_date)
            site: Site ID
            limit: Maximum number of sessions
            
        Returns:
            List of charging sessions
        """
        if end_date is None:
            end_date = start_date
        
        # Build API URL
        url = f"{self.api_url}/{site}"
        
        # Build query parameters
        params = {}
        
        # Date filtering
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        where_clause = (
            f'connectionTime>="{start_dt.strftime("%a, %d %b %Y 00:00:00 GMT")}" '
            f'and connectionTime<="{end_dt.strftime("%a, %d %b %Y 23:59:59 GMT")}"'
        )
        params["where"] = where_clause
        
        if limit:
            params["max_results"] = limit
        
        logger.info(f"Fetching sessions from {site} ({start_date} to {end_date})")
        
        # Make request
        data = self._make_request(url, params)
        sessions_data = data.get("_items", [])
        
        #Parse sessions
        sessions = []
        for item in sessions_data:
            try:
                session = self._parse_session(item)
                if session:
                    sessions.append(session)
            except Exception as e:
                logger.warning(f"Failed to parse session: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(sessions)} valid sessions")
        return sessions
    
    def _parse_session(self, data: dict) -> Optional[ChargingSession]:
        """Parse session data from API response."""
        required_fields = ["connectionTime", "disconnectTime", "kWhDelivered", "userID"]
        
        if not all(field in data for field in required_fields):
            return None
        
        if data["kWhDelivered"] <= 0:
            return None
        
        # Parse timestamps (RFC 1123 format)
        conn_time = datetime.strptime(data["connectionTime"], "%a, %d %b %Y %H:%M:%S %Z")
        disconn_time = datetime.strptime(data["disconnectTime"], "%a, %d %b %Y %H:%M:%S %Z")
        
        return ChargingSession(
            session_id=data.get("_id", "unknown"),
            user_id=data["userID"],
            connection_time=conn_time,
            disconnection_time=disconn_time,
            kwh_delivered=data["kWhDelivered"],
            site_name=data.get("siteName", "unknown")
        )
    
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
            site_max_power: Maximum site power
            time_horizon: Planning horizon
            
        Returns:
            Complete scenario
        """
        if not sessions:
            raise DataSourceError("Cannot build scenario from empty sessions list")
        
        logger.info(f"Building scenario from {len(sessions)} sessions")
        
        # Convert sessions to vehicles
        vehicles = []
        for session in sessions:
            try:
                vehicle = self._session_to_vehicle(session)
                vehicles.append(vehicle)
            except Exception as e:
                logger.warning(f"Failed to convert session to vehicle: {e}")
                continue
        
        # Generate price profile (TOU tariff)
        price_profile = self._generate_price_profile(time_horizon)
        
        scenario = Scenario(
            vehicles=vehicles,
            price_profile=price_profile,
            site_max_power=site_max_power,
            time_horizon=time_horizon,
            name=f"caltech_{sessions[0].connection_time.date()}"
        )
        
        logger.info(f"Built scenario with {len(vehicles)} vehicles")
        return scenario
    
    def _session_to_vehicle(self, session: ChargingSession) -> Vehicle:
        """Convert charging session to vehicle."""
        #Estimate SoC (we don't have real SoC data)
        battery_capacity = settings.battery_capacity
        soc_initial = np.random.uniform(0.1, 0.4)  # Assume arrives with low battery
        energy_delivered = session.kwh_delivered
        soc_gained = energy_delivered / battery_capacity
        soc_target = min(soc_initial + soc_gained, 1.0)
        
        return Vehicle(
            battery_capacity=battery_capacity,
            soc_initial=soc_initial,
            soc_target=soc_target,
            arrival_time=session.arrival_hour(),
            departure_time=session.departure_hour(),
            user_id=session.user_id,
            charging_power_min=settings.charging_power_min,
            charging_power_max=settings.charging_power_max
        )
    
    def _generate_price_profile(self, time_horizon: int) -> np.ndarray:
        """Generate TOU (Time of Use) price profile."""
        hours = np.arange(time_horizon)
        
        # California TOU rates
        prices = np.where(
            (hours >= 16) & (hours < 22), 0.30,  # On-Peak
            np.where(
                (hours >= 6) & (hours < 16), 0.18,  # Mid-Peak
                0.12  # Off-Peak
            )
        )
        
        return prices
