"""
Career database parser utility v2 with multi-backend support.

Handles loading and parsing of career database files from both YAML and SQLite backends.
Maintains backward compatibility with existing YAML-only parser.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import logging
import os

from .database_backend import get_storage_backend, StorageBackend

logger = logging.getLogger(__name__)


class CareerDatabaseError(Exception):
    """Custom exception for career database parsing errors."""
    pass


class CareerDatabaseParser:
    """Enhanced career database parser with multi-backend support."""
    
    def __init__(self, backend_type: Optional[str] = None):
        """Initialize parser with specified backend.
        
        Args:
            backend_type: Backend type ("yaml", "sqlite", or None for auto-detect)
        """
        self.backend_type = backend_type
        self._backend = None
    
    def load(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load career database from file.
        
        Args:
            path: Path to database file
            
        Returns:
            Dictionary containing parsed career data
            
        Raises:
            CareerDatabaseError: If file not found or parsing errors
        """
        path = Path(path)
        
        # Auto-detect backend type if not specified
        if self.backend_type is None:
            self.backend_type = self._detect_backend_type(path)
        
        # Get appropriate backend
        try:
            self._backend = get_storage_backend(self.backend_type)
        except ValueError as e:
            raise CareerDatabaseError(f"Invalid backend type: {e}")
        
        # Check if file exists
        if not self._backend.exists(path):
            raise CareerDatabaseError(f"Database file not found: {path}")
        
        # Load data
        try:
            data = self._backend.load(path)
            if data is None:
                raise CareerDatabaseError(f"Failed to load database from {path}")
            
            # Validate structure
            self._validate_structure(data)
            
            return data
            
        except Exception as e:
            raise CareerDatabaseError(f"Error loading database: {e}")
    
    def save(self, data: Dict[str, Any], path: Union[str, Path]) -> bool:
        """Save career database to file.
        
        Args:
            data: Career database dictionary
            path: Path to save to
            
        Returns:
            Success status
        """
        path = Path(path)
        
        # Auto-detect backend type from extension if not specified
        if self.backend_type is None:
            if path.suffix.lower() in ['.yaml', '.yml']:
                self.backend_type = 'yaml'
            elif path.suffix.lower() in ['.db', '.sqlite', '.sqlite3']:
                self.backend_type = 'sqlite'
            else:
                # Default to YAML
                self.backend_type = 'yaml'
        
        # Get appropriate backend
        try:
            self._backend = get_storage_backend(self.backend_type)
        except ValueError as e:
            logger.error(f"Invalid backend type: {e}")
            return False
        
        # Validate before saving
        try:
            self._validate_structure(data)
        except CareerDatabaseError as e:
            logger.error(f"Validation failed: {e}")
            return False
        
        # Save data
        return self._backend.save(data, path)
    
    def query_experiences(self, path: Union[str, Path], **filters) -> List[Dict[str, Any]]:
        """Query experiences from database.
        
        Args:
            path: Database path
            **filters: Query filters
            
        Returns:
            List of matching experiences
        """
        # For SQLite backend, use native query
        if self.backend_type == "sqlite":
            if self._backend is None:
                self._backend = get_storage_backend("sqlite")
            return self._backend.query_experiences(**filters)
        
        # For YAML, load all and filter in memory
        data = self.load(path)
        experiences = data.get("experiences", [])
        
        # Apply filters
        filtered = []
        for exp in experiences:
            match = True
            
            # Check each filter
            for key, value in filters.items():
                if key == "company" and exp.get("company") != value:
                    match = False
                    break
                elif key == "min_date" and exp.get("period"):
                    # Simple date comparison (would need proper parsing)
                    match = False
                    break
                # Add more filter logic as needed
            
            if match:
                filtered.append(exp)
        
        return filtered
    
    def _detect_backend_type(self, path: Path) -> str:
        """Auto-detect backend type from file extension."""
        suffix = path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            return 'yaml'
        elif suffix in ['.db', '.sqlite', '.sqlite3']:
            return 'sqlite'
        else:
            # Try to detect by content
            try:
                with open(path, 'rb') as f:
                    header = f.read(16)
                    if header.startswith(b'SQLite format'):
                        return 'sqlite'
            except:
                pass
            
            # Default to YAML
            return 'yaml'
    
    def _validate_structure(self, data: Dict[str, Any]):
        """Validate career database structure."""
        # Basic validation - ensure it's a dictionary
        if not isinstance(data, dict):
            raise CareerDatabaseError("Database must be a dictionary")
        
        # Check for at least one major section
        major_sections = ['experiences', 'education', 'skills', 'projects']
        if not any(section in data for section in major_sections):
            raise CareerDatabaseError(
                f"Database must contain at least one of: {', '.join(major_sections)}"
            )
        
        # Validate experiences structure
        if 'experiences' in data:
            if not isinstance(data['experiences'], list):
                raise CareerDatabaseError("Experiences must be a list")
            
            for i, exp in enumerate(data['experiences']):
                if not isinstance(exp, dict):
                    raise CareerDatabaseError(f"Experience {i} must be a dictionary")
                # Could add more field validation here
        
        # Validate education structure
        if 'education' in data:
            if not isinstance(data['education'], list):
                raise CareerDatabaseError("Education must be a list")
        
        # Validate skills structure
        if 'skills' in data:
            if not isinstance(data['skills'], dict):
                raise CareerDatabaseError("Skills must be a dictionary")


# Backward compatibility functions
def load_career_database(path: Union[str, Path]) -> Dict[str, Any]:
    """Load career database from file (backward compatible).
    
    Args:
        path: Path to database file
        
    Returns:
        Dictionary containing parsed career data
    """
    parser = CareerDatabaseParser()
    return parser.load(path)


def save_career_database(data: Dict[str, Any], path: Union[str, Path]) -> bool:
    """Save career database to file (backward compatible).
    
    Args:
        data: Career database dictionary
        path: Path to save to
        
    Returns:
        Success status
    """
    parser = CareerDatabaseParser()
    return parser.save(data, path)


# Configuration support
def get_default_backend() -> str:
    """Get default backend type from environment or config."""
    return os.environ.get('CAREER_DB_BACKEND', 'yaml').lower()


def set_default_backend(backend_type: str):
    """Set default backend type in environment."""
    os.environ['CAREER_DB_BACKEND'] = backend_type