"""
Database migration utilities for converting between storage backends.

This module provides tools to migrate career databases between different
storage formats (YAML <-> SQLite).
"""

import logging
from pathlib import Path
from typing import Union, Optional
from datetime import datetime

from .database_backend import get_storage_backend, StorageBackend

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles migration between different database backends."""
    
    def __init__(self):
        """Initialize the migrator."""
        self.backends = {
            "yaml": get_storage_backend("yaml"),
            "sqlite": get_storage_backend("sqlite")
        }
    
    def migrate(
        self,
        source_path: Union[str, Path],
        source_type: str,
        dest_path: Union[str, Path],
        dest_type: str,
        backup: bool = True
    ) -> bool:
        """Migrate database from one backend to another.
        
        Args:
            source_path: Source database path
            source_type: Source backend type ("yaml" or "sqlite")
            dest_path: Destination database path
            dest_type: Destination backend type ("yaml" or "sqlite")
            backup: Whether to create backup before migration
            
        Returns:
            Success status
        """
        try:
            # Validate backend types
            if source_type not in self.backends:
                raise ValueError(f"Invalid source type: {source_type}")
            if dest_type not in self.backends:
                raise ValueError(f"Invalid destination type: {dest_type}")
            
            source_backend = self.backends[source_type]
            dest_backend = self.backends[dest_type]
            
            # Check if source exists
            if not source_backend.exists(source_path):
                logger.error(f"Source database not found: {source_path}")
                return False
            
            # Create backup if requested
            if backup:
                backup_path = self._create_backup_path(source_path)
                if not source_backend.backup(source_path, backup_path):
                    logger.warning("Failed to create backup, continuing anyway")
            
            # Load data from source
            logger.info(f"Loading data from {source_type} at {source_path}")
            data = source_backend.load(source_path)
            
            if data is None:
                logger.error("Failed to load source data")
                return False
            
            # Check if destination already exists
            if dest_backend.exists(dest_path):
                logger.warning(f"Destination already exists: {dest_path}")
                # Create backup of destination
                if backup:
                    dest_backup = self._create_backup_path(dest_path)
                    dest_backend.backup(dest_path, dest_backup)
            
            # Save to destination
            logger.info(f"Saving data to {dest_type} at {dest_path}")
            if not dest_backend.save(data, dest_path):
                logger.error("Failed to save to destination")
                return False
            
            # Verify migration
            logger.info("Verifying migration...")
            verified_data = dest_backend.load(dest_path)
            
            if verified_data is None:
                logger.error("Failed to verify migration - could not load destination")
                return False
            
            # Basic verification - check key counts
            if not self._verify_migration(data, verified_data):
                logger.error("Migration verification failed")
                return False
            
            logger.info(f"Successfully migrated from {source_type} to {dest_type}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _create_backup_path(self, original_path: Union[str, Path]) -> Path:
        """Create a backup path with timestamp."""
        path = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
        return path.parent / backup_name
    
    def _verify_migration(self, source_data: dict, dest_data: dict) -> bool:
        """Verify that migration preserved all data."""
        # Check top-level keys
        if set(source_data.keys()) != set(dest_data.keys()):
            logger.error("Top-level keys don't match")
            return False
        
        # Check counts for list fields
        for key in ["experiences", "education", "projects"]:
            if key in source_data:
                source_count = len(source_data[key])
                dest_count = len(dest_data.get(key, []))
                if source_count != dest_count:
                    logger.error(f"{key} count mismatch: {source_count} vs {dest_count}")
                    return False
        
        # Check skills
        if "skills" in source_data:
            source_skills = source_data["skills"]
            dest_skills = dest_data.get("skills", {})
            if set(source_skills.keys()) != set(dest_skills.keys()):
                logger.error("Skills categories don't match")
                return False
        
        return True


def migrate_yaml_to_sqlite(
    yaml_path: Union[str, Path],
    sqlite_path: Union[str, Path],
    backup: bool = True
) -> bool:
    """Convenience function to migrate from YAML to SQLite.
    
    Args:
        yaml_path: Path to YAML file
        sqlite_path: Path for SQLite database
        backup: Whether to create backup
        
    Returns:
        Success status
    """
    migrator = DatabaseMigrator()
    return migrator.migrate(yaml_path, "yaml", sqlite_path, "sqlite", backup)


def migrate_sqlite_to_yaml(
    sqlite_path: Union[str, Path],
    yaml_path: Union[str, Path],
    backup: bool = True
) -> bool:
    """Convenience function to migrate from SQLite to YAML.
    
    Args:
        sqlite_path: Path to SQLite database
        yaml_path: Path for YAML file
        backup: Whether to create backup
        
    Returns:
        Success status
    """
    migrator = DatabaseMigrator()
    return migrator.migrate(sqlite_path, "sqlite", yaml_path, "yaml", backup)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate career database between different storage backends"
    )
    parser.add_argument("source", help="Source database path")
    parser.add_argument("source_type", choices=["yaml", "sqlite"], 
                       help="Source database type")
    parser.add_argument("dest", help="Destination database path")
    parser.add_argument("dest_type", choices=["yaml", "sqlite"],
                       help="Destination database type")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip creating backups")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Perform migration
    migrator = DatabaseMigrator()
    success = migrator.migrate(
        args.source,
        args.source_type,
        args.dest,
        args.dest_type,
        backup=not args.no_backup
    )
    
    exit(0 if success else 1)