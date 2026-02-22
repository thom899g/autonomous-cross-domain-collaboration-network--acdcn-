"""
Firebase Client Manager
Handles Firestore initialization, connection pooling, and error recovery.
CRITICAL: Following mission constraint to use firebase-admin for ALL database needs.
"""
import firebase_admin
from firebase_admin import credentials, firestore, exceptions
from typing import Optional, Dict, Any
import structlog
from datetime import datetime, timedelta
from threading import Lock

from config import get_config

logger = structlog.get_logger()

class FirebaseManager:
    """
    Manages Firebase Firestore connection with connection pooling and automatic retry.
    Implements singleton pattern to prevent multiple app initializations.
    """
    
    _instance: Optional['FirebaseManager'] = None
    _lock: Lock = Lock()
    
    def __new__(cls):
        """Thread-safe singleton implementation"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FirebaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Lazy initialization to avoid circular imports"""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._config = get_config()
            self._app: Optional[firebase_admin.App] = None
            self._db: Optional[firestore.Client] = None
            self._connection_stats: Dict[str, Any] = {
                'last_healthy_check': None,
                'error_count': 0,
                'total_operations': 0
            }
            self._initialized = True
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK with error handling"""
        if self._