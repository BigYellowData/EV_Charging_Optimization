"""
Cache interface for flexible caching strategies.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import timedelta


class ICache(ABC):
    """Interface for caching implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live (optional)
        """
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all cached data."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
