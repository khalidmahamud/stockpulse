"""
Configuration management for StockPulse.

Loads settings from environment variables and YAML config files.
"""

import os
from pathlib import Path
from functools import lru_cache

import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


# Load .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    url: str = Field(alias="DATABASE_URL")

    class Config:
        populate_by_name = True


class APIKeySettings(BaseSettings):
    """External API credentials."""

    finnhub: str = Field(alias="FINNHUB_API_KEY")
    alpha_vantage: str = Field(alias="ALPHA_VANTAGE_API_KEY")

    class Config:
        populate_by_name = True


class AppSettings(BaseSettings):
    """Application-level settings."""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000", alias="MLFLOW_TRACKING_URI"
    )

    class Config:
        populate_by_name = True

@lru_cache()
def get_config(config_name: str = "base") -> dict:
    """Load a YAML configuration file."""
    config_path = PROJECT_ROOT / "configs" / f"{config_name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    """Get database settings, cached for performance."""
    return DatabaseSettings()

@lru_cache()
def get_api_key_settings() -> APIKeySettings:
    """Get API key settings, cached for performance."""
    return APIKeySettings()

@lru_cache()
def get_app_settings() -> AppSettings:
    """Get application settings, cached for performance."""
    return AppSettings()    

