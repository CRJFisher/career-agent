"""Configuration module for Career Application Agent."""

from .database_config import (
    DatabaseConfig,
    get_database_config,
    get_backend_type,
    get_database_path,
    switch_to_sqlite,
    switch_to_yaml
)

__all__ = [
    'DatabaseConfig',
    'get_database_config',
    'get_backend_type',
    'get_database_path',
    'switch_to_sqlite',
    'switch_to_yaml'
]