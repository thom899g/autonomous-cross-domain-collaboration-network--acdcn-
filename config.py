"""
ACDCN Configuration Management
Centralized configuration with environment variable support and validation.
"""
import os
from typing import Dict, Any
from pydantic import BaseSettings, Field, validator
import structlog

logger = structlog.get_logger()

class ACDCNConfig(BaseSettings):
    """Validated configuration for the ACDCN ecosystem"""
    
    # Firebase Configuration (CRITICAL - following mission constraints)
    firebase_credential_path: str = Field(
        default="firebase-credentials.json",
        description="Path to Firebase service account credentials"
    )
    firestore_database_name: str = Field(
        default="(default)",
        description="Firestore database instance name"
    )
    
    # Knowledge Graph Configuration
    kg_synergy_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum synergy score for collaboration consideration"
    )
    max_domain_connections: int = Field(
        default=50,
        gt=0,
        description="Maximum connections per domain to prevent overfitting"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API binding host")
    api_port: int = Field(default=8000, gt=1024, lt=65536, description="API port")
    
    # Performance Configuration
    batch_size: int = Field(
        default=100,
        gt=0,
        description="Firestore batch operations size"
    )
    max_retry_attempts: int = Field(
        default=3,
        ge=1,
        description="Maximum retry attempts for transient failures"
    )
    
    # Validation
    @validator('firebase_credential_path')
    def validate_firebase_credential_path(cls, v: str) -> str:
        """Ensure Firebase credential file exists before initialization"""
        if not os.path.exists(v):
            logger.error("firebase_credential_missing", path=v)
            raise FileNotFoundError(
                f"Firebase credential file not found at {v}. "
                "Generate via: https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk"
            )
        return v
    
    class Config:
        env_prefix = "ACDCN_"
        case_sensitive = False
        env_file = ".env"

# Singleton configuration instance with lazy initialization
_config: ACDCNConfig = None

def get_config() -> ACDCNConfig:
    """
    Get or initialize the global configuration.
    Implements singleton pattern with thread safety consideration.
    """
    global _config
    if _config is None:
        try:
            _config = ACDCNConfig()
            logger.info("configuration_loaded", config=_config.dict(exclude={'firebase_credential_path'}))
        except Exception as e:
            logger.critical("configuration_failed", error=str(e))
            raise
    return _config