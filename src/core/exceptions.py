"""Custom exceptions for the application."""


class EVChargingError(Exception):
    """Base exception for EV charging optimization errors."""
    pass


class OptimizationError(EVChargingError):
    """Raised when optimization fails."""
    pass


class DataSourceError(EVChargingError):
    """Raised when data source operations fail."""
    pass


class ValidationError(EVChargingError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(EVChargingError):
    """Raised when configuration is invalid."""
    pass


class CacheError(EVChargingError):
    """Raised when cache operations fail."""
    pass
