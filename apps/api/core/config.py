"""Configuration module - re-exports settings from parent config."""
from ..config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
