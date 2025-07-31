"""
Career database parser utility.

Handles loading and parsing of YAML-based career database files.
Supports both single files and directories of YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import logging

logger = logging.getLogger(__name__)


class CareerDatabaseError(Exception):
    """Custom exception for career database parsing errors."""
    pass


def load_career_database(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load career database from YAML file or directory.
    
    Args:
        path: Path to YAML file or directory containing YAML files
        
    Returns:
        Dictionary containing parsed career data
        
    Raises:
        CareerDatabaseError: If file not found, invalid YAML, or other parsing errors
        
    Expected YAML structure:
        personal_info:
            name: str
            email: str
            phone: str
            location: str
            
        experience:
            - title: str
              company: str
              duration: str
              description: str
              achievements: List[str]
              technologies: List[str]
              
        education:
            - degree: str
              institution: str
              year: str
              details: str
              
        skills:
            technical: List[str]
            soft: List[str]
            languages: List[str]
            
        projects:
            - name: str
              description: str
              technologies: List[str]
              outcomes: List[str]
    """
    path = Path(path)
    
    if not path.exists():
        raise CareerDatabaseError(f"Path does not exist: {path}")
    
    try:
        if path.is_file():
            return _load_single_file(path)
        elif path.is_dir():
            return _load_directory(path)
        else:
            raise CareerDatabaseError(f"Path is neither file nor directory: {path}")
            
    except yaml.YAMLError as e:
        raise CareerDatabaseError(f"Invalid YAML format: {e}")
    except Exception as e:
        raise CareerDatabaseError(f"Error loading career database: {e}")


def _load_single_file(file_path: Path) -> Dict[str, Any]:
    """Load a single YAML file."""
    if not file_path.suffix.lower() in ['.yaml', '.yml']:
        raise CareerDatabaseError(f"File must have .yaml or .yml extension: {file_path}")
    
    logger.info(f"Loading career database from: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    if not isinstance(data, dict):
        raise CareerDatabaseError(f"YAML file must contain a dictionary at root level")
        
    return data


def _load_directory(dir_path: Path) -> Dict[str, Any]:
    """Load and merge all YAML files from a directory."""
    yaml_files = list(dir_path.glob('*.yaml')) + list(dir_path.glob('*.yml'))
    
    if not yaml_files:
        raise CareerDatabaseError(f"No YAML files found in directory: {dir_path}")
    
    logger.info(f"Found {len(yaml_files)} YAML files in: {dir_path}")
    
    merged_data = {}
    
    for file_path in sorted(yaml_files):
        file_data = _load_single_file(file_path)
        
        # Merge data with conflict detection
        for key, value in file_data.items():
            if key in merged_data:
                logger.warning(f"Key '{key}' already exists, will be overwritten by: {file_path}")
            merged_data[key] = value
    
    return merged_data


def validate_career_database(data: Dict[str, Any]) -> List[str]:
    """
    Validate career database structure and return list of warnings.
    
    Args:
        data: Parsed career database dictionary
        
    Returns:
        List of validation warnings (empty if all valid)
    """
    warnings = []
    
    # Check recommended top-level keys
    recommended_keys = ['personal_info', 'experience', 'education', 'skills']
    for key in recommended_keys:
        if key not in data:
            warnings.append(f"Recommended key '{key}' not found in career database")
    
    # Validate personal_info
    if 'personal_info' in data:
        personal = data['personal_info']
        if not isinstance(personal, dict):
            warnings.append("'personal_info' should be a dictionary")
        else:
            for field in ['name', 'email']:
                if field not in personal:
                    warnings.append(f"Recommended field 'personal_info.{field}' not found")
    
    # Validate experience
    if 'experience' in data:
        exp = data['experience']
        if not isinstance(exp, list):
            warnings.append("'experience' should be a list of experience entries")
        elif exp:
            for i, entry in enumerate(exp):
                if not isinstance(entry, dict):
                    warnings.append(f"Experience entry {i} should be a dictionary")
                elif 'title' not in entry or 'company' not in entry:
                    warnings.append(f"Experience entry {i} missing 'title' or 'company'")
    
    return warnings


def merge_career_databases(*databases: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple career databases into one.
    
    Args:
        *databases: Variable number of career database dictionaries
        
    Returns:
        Merged career database dictionary
        
    Note:
        Later databases override earlier ones for conflicting keys.
        Lists are concatenated rather than replaced.
    """
    merged = {}
    
    for db in databases:
        for key, value in db.items():
            if key in merged and isinstance(merged[key], list) and isinstance(value, list):
                # Concatenate lists
                merged[key] = merged[key] + value
            else:
                # Override with new value
                merged[key] = value
    
    return merged