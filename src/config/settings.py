"""
Centralized application settings using Pydantic.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # API Configuration
    caltech_api_url: str = Field(
        default="https://ev.caltech.edu/api/v1/sessions",
        description="Base URL for Caltech ACN-Data API"
    )
    caltech_api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for Caltech authentication"
    )
    caltech_site: str = Field(
        default="caltech",
        description="Caltech site ID (caltech, jpl, office001)"
    )
    caltech_date: str = Field(
        default="2019-07-15",
        description="Date for real data (YYYY-MM-DD)"
    )
    caltech_limit: Optional[int] = Field(
        default=30,
        description="Max number of vehicles to fetch from Caltech API",
        ge=1
    )
    
    # Optimization Parameters
    n_vehicles: int = Field(default=30, description="Number of vehicles (synthetic mode)", ge=1)
    t_horizon: int = Field(default=24, description="Time horizon in hours", ge=1, le=168)
    dt: float = Field(default=1.0, description="Time step in hours", gt=0)
    
    # Battery & Power
    battery_capacity: float = Field(default=30.0, description="Default battery capacity in kWh", gt=0)
    charging_power_min: float = Field(default=-6.0, description="Min charging power (V2G) in kW")
    charging_power_max: float = Field(default=30.0, description="Max charging power in kW", gt=0)
    site_max_power: float = Field(default=60.0, description="Site transformer capacity in kW", gt=0)
    
    # MODE Algorithm Parameters (Multi-Objective Differential Evolution)
    mode_pop_size: int = Field(default=100, description="Population size", ge=10)
    mode_n_gen: int = Field(default=1500, description="Number of generations", ge=100)
    mode_variant: str = Field(default="DE/rand/1/bin", description="DE variant")
    mode_cr: float = Field(default=0.9, description="Crossover rate", ge=0, le=1)
    mode_f: float = Field(default=0.5, description="Mutation factor", ge=0, le=2)
    
    # Infrastructure
    cache_dir: Path = Field(default=Path("data_cache"), description="Cache directory path")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds", ge=0)
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Log file path")
    
    # Application
    app_name: str = Field(default="EV Charging Optimizer", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/production)")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables
        
    def get_api_key(self) -> str:
        """Get API key as string (raises if not set)."""
        if not self.caltech_api_key:
            raise ValueError("CALTECH_API_KEY not configured")
        return self.caltech_api_key.get_secret_value()
    
    def get_optimizer_config(self) -> dict:
        """Get MODE optimizer configuration."""
        return {
            'pop_size': self.mode_pop_size,
            'n_gen': self.mode_n_gen,
            'variant': self.mode_variant,
            'CR': self.mode_cr,
            'F': self.mode_f
        }


# Global settings instance
settings = Settings()
