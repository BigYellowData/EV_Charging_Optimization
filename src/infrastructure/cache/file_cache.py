"""
File-based cache implementation.
"""
import json
import pickle
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...core.interfaces.cache import ICache
from ...core.exceptions import CacheError
from ...config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    timestamp: datetime
    ttl: Optional[timedelta] = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return datetime.now() > self.timestamp + self.ttl


class FileCache(ICache):
    """File-based caching implementation."""
    
    def __init__(
        self,
        cache_dir: Path,
        default_ttl: Optional[timedelta] = None,
        use_pickle: bool = False
    ):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live
            use_pickle: Use pickle instead of JSON (allows caching any object)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.use_pickle = use_pickle
        
        logger.info(f"Initialized FileCache at {self.cache_dir}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        extension = ".pkl" if self.use_pickle else ".json"
        return self.cache_dir / f"{safe_key}{extension}"
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss: {key}")
            return None
        
        try:
            # Load cache entry
            if self.use_pickle:
                with open(cache_path, "rb") as f:
                    entry = pickle.load(f)
            else:
                with open(cache_path, "r") as f:
                    data = json.load(f)
                    entry = CacheEntry(
                        value=data["value"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        ttl=timedelta(seconds=data["ttl"]) if data.get("ttl") else None
                    )
            
            # Check expiration
            if entry.is_expired():
                logger.debug(f"Cache expired: {key}")
                self.delete(key)
                return None
            
            logger.debug(f"Cache hit: {key}")
            return entry.value
            
        except Exception as e:
            logger.error(f"Cache read error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Store value in cache."""
        cache_path = self._get_cache_path(key)
        
        ttl = ttl or self.default_ttl
        
        entry = CacheEntry(
            value=value,
            timestamp=datetime.now(),
            ttl=ttl
        )
        
        try:
            if self.use_pickle:
                with open(cache_path, "wb") as f:
                    pickle.dump(entry, f)
            else:
                data = {
                    "value": value,
                    "timestamp": entry.timestamp.isoformat(),
                    "ttl": ttl.total_seconds() if ttl else None
                }
                with open(cache_path, "w") as f:
                    json.dump(data, f, indent=2)
            
            logger.debug(f"Cached: {key}")
            
        except Exception as e:
            logger.error(f"Cache write error for {key}: {e}")
            raise CacheError(f"Failed to cache {key}: {e}")
    
    def delete(self, key: str):
        """Delete key from cache."""
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache: {key}")
    
    def clear(self):
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                cache_file.unlink()
        
        logger.info("Cache cleared")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self._get_cache_path(key).exists()
