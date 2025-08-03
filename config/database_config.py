"""
Database configuration for Career Application Agent.

This module manages database backend configuration and provides
utilities for switching between YAML and SQLite storage.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Manages database backend configuration."""
    
    CONFIG_FILE = Path.home() / ".career-agent" / "config.json"
    
    def __init__(self):
        """Initialize database configuration."""
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        # Return default config
        return {
            "database": {
                "backend": "yaml",
                "yaml_path": str(Path.home() / ".career-agent" / "career_database.yaml"),
                "sqlite_path": str(Path.home() / ".career-agent" / "career_database.db")
            }
        }
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    @property
    def backend_type(self) -> str:
        """Get current backend type."""
        # Check environment variable first
        env_backend = os.environ.get('CAREER_DB_BACKEND')
        if env_backend:
            return env_backend.lower()
        
        # Then check config file
        return self._config.get("database", {}).get("backend", "yaml")
    
    @backend_type.setter
    def backend_type(self, value: str):
        """Set backend type."""
        if value not in ["yaml", "sqlite"]:
            raise ValueError(f"Invalid backend type: {value}")
        
        if "database" not in self._config:
            self._config["database"] = {}
        
        self._config["database"]["backend"] = value
        self._save_config()
    
    @property
    def database_path(self) -> Path:
        """Get path for current backend."""
        backend = self.backend_type
        
        if backend == "yaml":
            return Path(self._config.get("database", {}).get(
                "yaml_path",
                str(Path.home() / ".career-agent" / "career_database.yaml")
            ))
        elif backend == "sqlite":
            return Path(self._config.get("database", {}).get(
                "sqlite_path",
                str(Path.home() / ".career-agent" / "career_database.db")
            ))
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def set_database_path(self, backend: str, path: Union[str, Path]):
        """Set database path for specific backend."""
        if backend not in ["yaml", "sqlite"]:
            raise ValueError(f"Invalid backend type: {backend}")
        
        if "database" not in self._config:
            self._config["database"] = {}
        
        self._config["database"][f"{backend}_path"] = str(path)
        self._save_config()
    
    def get_all_paths(self) -> Dict[str, Path]:
        """Get all configured database paths."""
        return {
            "yaml": Path(self._config.get("database", {}).get(
                "yaml_path",
                str(Path.home() / ".career-agent" / "career_database.yaml")
            )),
            "sqlite": Path(self._config.get("database", {}).get(
                "sqlite_path",
                str(Path.home() / ".career-agent" / "career_database.db")
            ))
        }
    
    def switch_backend(self, new_backend: str, migrate_data: bool = True) -> bool:
        """Switch to a different backend, optionally migrating data.
        
        Args:
            new_backend: Backend to switch to ("yaml" or "sqlite")
            migrate_data: Whether to migrate existing data
            
        Returns:
            Success status
        """
        if new_backend == self.backend_type:
            logger.info(f"Already using {new_backend} backend")
            return True
        
        old_backend = self.backend_type
        old_path = self.database_path
        
        # Update backend type
        self.backend_type = new_backend
        new_path = self.database_path
        
        # Migrate data if requested
        if migrate_data and old_path.exists():
            logger.info(f"Migrating data from {old_backend} to {new_backend}")
            
            try:
                from ..utils.database_migration import DatabaseMigrator
                migrator = DatabaseMigrator()
                
                success = migrator.migrate(
                    old_path, old_backend,
                    new_path, new_backend,
                    backup=True
                )
                
                if not success:
                    # Rollback backend change
                    self.backend_type = old_backend
                    logger.error("Migration failed, rolled back to previous backend")
                    return False
                
                logger.info("Migration completed successfully")
                
            except Exception as e:
                # Rollback backend change
                self.backend_type = old_backend
                logger.error(f"Migration failed: {e}")
                return False
        
        return True


# Global instance
_config = None


def get_database_config() -> DatabaseConfig:
    """Get global database configuration instance."""
    global _config
    if _config is None:
        _config = DatabaseConfig()
    return _config


# Convenience functions
def get_backend_type() -> str:
    """Get current database backend type."""
    return get_database_config().backend_type


def get_database_path() -> Path:
    """Get current database path."""
    return get_database_config().database_path


def switch_to_sqlite(migrate: bool = True) -> bool:
    """Switch to SQLite backend."""
    return get_database_config().switch_backend("sqlite", migrate)


def switch_to_yaml(migrate: bool = True) -> bool:
    """Switch to YAML backend."""
    return get_database_config().switch_backend("yaml", migrate)