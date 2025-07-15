"""
Cache Storage Service - Handles Redis and database fallback storage
Provides unified cache interface with TTL management and concurrency control
"""

import json
import logging
import time
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Try to import Redis, but handle gracefully if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

# Database model for cache fallback
Base = declarative_base()


class PropertyCache(Base):
    """Database model for property cache fallback"""
    __tablename__ = 'property_cache'
    
    key = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_property_cache_fetched_at', 'fetched_at'),
    )


class CacheStorageService:
    """
    Unified cache storage with Redis primary and database fallback
    """
    
    def __init__(self):
        self.redis_client = None
        self.db_engine = None
        self.Session = None
        self.ttl_hours = int(os.getenv('CACHE_TTL_HOURS', '24'))
        self.max_ttl_hours = int(os.getenv('CACHE_MAX_TTL_HOURS', '72'))
        
        # Initialize Redis connection
        self._initialize_redis()
        
        # Initialize database connection
        self._initialize_database()
    
    def _initialize_redis(self):
        """Initialize Redis connection if available"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using database-only caching")
            return
        
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}, falling back to database")
            self.redis_client = None
    
    def _initialize_database(self):
        """Initialize database connection for cache fallback"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            self.db_engine = create_engine(
                database_url,
                pool_recycle=300,
                pool_pre_ping=True,
                connect_args={"sslmode": "require"} if "postgres" in database_url else {}
            )
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.db_engine)
            
            self.Session = sessionmaker(bind=self.db_engine)
            logger.info("Database cache fallback initialized")
            
        except Exception as e:
            logger.error(f"Database cache initialization failed: {e}")
            raise
    
    @contextmanager
    def get_db_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key, trying Redis first, then database
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if found and valid, None otherwise
        """
        # Try Redis first
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    payload = json.loads(cached_data)
                    if self._is_cache_valid(payload):
                        logger.debug(f"Cache hit (Redis): {key}")
                        return payload
                    else:
                        # Remove expired data
                        self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Try database fallback
        try:
            with self.get_db_session() as session:
                cache_entry = session.query(PropertyCache).filter_by(key=key).first()
                if cache_entry:
                    payload = {
                        'payload': cache_entry.payload,
                        'fetched_at': cache_entry.fetched_at.timestamp()
                    }
                    
                    if self._is_cache_valid(payload):
                        logger.debug(f"Cache hit (Database): {key}")
                        
                        # Update Redis cache if available
                        if self.redis_client:
                            try:
                                self.redis_client.setex(
                                    key, 
                                    self.ttl_hours * 3600,
                                    json.dumps(payload)
                                )
                            except Exception as e:
                                logger.warning(f"Redis update failed: {e}")
                        
                        return payload
                    else:
                        # Remove expired data
                        session.delete(cache_entry)
                        session.commit()
        except Exception as e:
            logger.warning(f"Database get failed: {e}")
        
        return None
    
    def set(self, key: str, data: Dict[str, Any], ttl_hours: Optional[int] = None) -> bool:
        """
        Set cached data with given key and TTL
        
        Args:
            key: Cache key
            data: Data to cache
            ttl_hours: TTL in hours (defaults to configured TTL)
            
        Returns:
            True if successful, False otherwise
        """
        if ttl_hours is None:
            ttl_hours = self.ttl_hours
        
        # Prepare payload
        payload = {
            'payload': data,
            'fetched_at': time.time()
        }
        
        success = False
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, 
                    ttl_hours * 3600,
                    json.dumps(payload)
                )
                success = True
                logger.debug(f"Cache set (Redis): {key}")
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        # Always save to database as well
        try:
            with self.get_db_session() as session:
                cache_entry = session.query(PropertyCache).filter_by(key=key).first()
                
                if cache_entry:
                    cache_entry.payload = data
                    cache_entry.fetched_at = datetime.utcnow()
                else:
                    cache_entry = PropertyCache(
                        key=key,
                        payload=data,
                        fetched_at=datetime.utcnow()
                    )
                    session.add(cache_entry)
                
                session.commit()
                success = True
                logger.debug(f"Cache set (Database): {key}")
                
        except Exception as e:
            logger.warning(f"Database set failed: {e}")
        
        return success
    
    def delete(self, key: str) -> bool:
        """
        Delete cached data by key
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        success = False
        
        # Delete from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        # Delete from database
        try:
            with self.get_db_session() as session:
                cache_entry = session.query(PropertyCache).filter_by(key=key).first()
                if cache_entry:
                    session.delete(cache_entry)
                    session.commit()
                    success = True
        except Exception as e:
            logger.warning(f"Database delete failed: {e}")
        
        return success
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and is valid
        """
        return self.get(key) is not None
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        
        # Clear from database
        try:
            with self.get_db_session() as session:
                expiry_time = datetime.utcnow() - timedelta(hours=self.max_ttl_hours)
                
                result = session.query(PropertyCache).filter(
                    PropertyCache.fetched_at < expiry_time
                ).delete()
                
                session.commit()
                cleared = result
                logger.info(f"Cleared {cleared} expired cache entries")
                
        except Exception as e:
            logger.warning(f"Failed to clear expired entries: {e}")
        
        return cleared

    def clear_all(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        
        # Clear from database
        try:
            with self.get_db_session() as session:
                result = session.query(PropertyCache).delete()
                session.commit()
                cleared = result
                logger.info(f"Cleared {cleared} total cache entries")
                
        except Exception as e:
            logger.warning(f"Failed to clear all cache entries: {e}")
        
        return cleared
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'redis_available': self.redis_client is not None,
            'ttl_hours': self.ttl_hours,
            'max_ttl_hours': self.max_ttl_hours,
            'total_entries': 0,
            'redis_entries': 0
        }
        
        # Database stats
        try:
            with self.get_db_session() as session:
                stats['total_entries'] = session.query(PropertyCache).count()
        except Exception as e:
            logger.warning(f"Failed to get database stats: {e}")
        
        # Redis stats
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_entries'] = info.get('db0', {}).get('keys', 0)
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
        
        return stats
    
    def set_with_lock(self, key: str, data: Dict[str, Any], lock_timeout: int = 30) -> bool:
        """
        Set data with distributed lock to prevent concurrent updates
        
        Args:
            key: Cache key
            data: Data to cache
            lock_timeout: Lock timeout in seconds
            
        Returns:
            True if set successfully, False if locked
        """
        lock_key = f"lock:{key}"
        
        # Try to acquire lock
        if self.redis_client:
            try:
                if self.redis_client.set(lock_key, "locked", nx=True, ex=lock_timeout):
                    try:
                        # Set the data
                        result = self.set(key, data)
                        return result
                    finally:
                        # Always release the lock
                        self.redis_client.delete(lock_key)
                else:
                    logger.debug(f"Cache key {key} is locked, skipping update")
                    return False
            except Exception as e:
                logger.warning(f"Lock operation failed: {e}")
        
        # Fallback to regular set if Redis not available
        return self.set(key, data)
    
    def _is_cache_valid(self, payload: Dict[str, Any]) -> bool:
        """
        Check if cached payload is still valid based on TTL
        
        Args:
            payload: Cached payload with fetched_at timestamp
            
        Returns:
            True if cache is still valid
        """
        if not payload or 'fetched_at' not in payload:
            return False
        
        current_time = time.time()
        cache_time = payload['fetched_at']
        
        # Check if within TTL
        ttl_seconds = self.ttl_hours * 3600
        return (current_time - cache_time) <= ttl_seconds
    
    def get_stale_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get stale data for stale-while-revalidate pattern
        
        Args:
            key: Cache key
            
        Returns:
            Stale data if available, None otherwise
        """
        # Check database for stale data (up to max_ttl_hours)
        try:
            with self.get_db_session() as session:
                cache_entry = session.query(PropertyCache).filter_by(key=key).first()
                if cache_entry:
                    payload = {
                        'payload': cache_entry.payload,
                        'fetched_at': cache_entry.fetched_at.timestamp()
                    }
                    
                    current_time = time.time()
                    cache_time = payload['fetched_at']
                    
                    # Check if within max TTL (for stale data)
                    max_ttl_seconds = self.max_ttl_hours * 3600
                    if (current_time - cache_time) <= max_ttl_seconds:
                        return payload
                    else:
                        # Remove very old data
                        session.delete(cache_entry)
                        session.commit()
        except Exception as e:
            logger.warning(f"Failed to get stale data: {e}")
        
        return None


# Global instance
_cache_service = None


def get_cache_service() -> CacheStorageService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheStorageService()
    return _cache_service