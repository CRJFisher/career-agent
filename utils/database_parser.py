"""
Career database parser utility.

Handles loading and parsing of YAML-based career database files.
Supports both single files and directories of YAML files.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import logging
import jsonschema

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
            linkedin: str (optional)
            github: str (optional)
            website: str (optional)
            
        experience:
            - title: str
              company: str
              duration: str
              location: str (optional)
              description: str
              achievements: List[str]
              technologies: List[str] (optional)
              team_size: int (optional)
              reason_for_leaving: str (optional)
              company_culture_pros: List[str] (optional)
              company_culture_cons: List[str] (optional)
              projects: List[Dict] (optional)
                - title: str
                  description: str
                  achievements: List[str]
                  role: str (optional)
                  technologies: List[str] (optional)
                  key_stakeholders: List[str] (optional)
                  notable_challenges: List[str] (optional)
                  direct_reports: int (optional)
                  reports_to: str (optional)
              
        education:
            - degree: str
              institution: str
              year: str
              location: str (optional)
              gpa: str (optional)
              honors: str (optional)
              details: str (optional)
              coursework: List[str] (optional)
              
        skills:
            technical: List[str]
            soft: List[str] (optional)
            languages: List[str] (optional)
            tools: List[str] (optional)
            frameworks: List[str] (optional)
            methodologies: List[str] (optional)
            
        projects:
            - name: str
              type: str (personal, open_source, freelance, hackathon, academic, volunteer)
              description: str
              role: str (optional)
              duration: str (optional)
              technologies: List[str]
              outcomes: List[str]
              url: str (optional)
              context: str (optional)
              team_size: int (optional)
              users: str (optional)
              
        certifications: List[Dict] (optional)
            - name: str
              issuer: str
              year: str
              expiry: str (optional)
              credential_id: str (optional)
              url: str (optional)
              
        publications: List[Dict] (optional)
            - title: str
              venue: str
              year: str
              type: str (optional)
              url: str (optional)
              coauthors: List[str] (optional)
              
        awards: List[Dict] (optional)
            - name: str
              organization: str
              year: str
              description: str (optional)
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
                else:
                    # Check required fields
                    if 'title' not in entry or 'company' not in entry:
                        warnings.append(f"Experience entry {i} missing 'title' or 'company'")
                    
                    # Validate nested projects if present
                    if 'projects' in entry:
                        if not isinstance(entry['projects'], list):
                            warnings.append(f"Experience entry {i} 'projects' should be a list")
                        else:
                            for j, proj in enumerate(entry['projects']):
                                if not isinstance(proj, dict):
                                    warnings.append(f"Experience entry {i} project {j} should be a dictionary")
                                elif 'title' not in proj or 'description' not in proj or 'achievements' not in proj:
                                    warnings.append(f"Experience entry {i} project {j} missing required fields")
    
    # Validate standalone projects
    if 'projects' in data:
        projects = data['projects']
        if not isinstance(projects, list):
            warnings.append("'projects' should be a list of project entries")
        elif projects:
            valid_types = ['personal', 'open_source', 'freelance', 'hackathon', 'academic', 'volunteer']
            for i, proj in enumerate(projects):
                if not isinstance(proj, dict):
                    warnings.append(f"Project entry {i} should be a dictionary")
                else:
                    # Check required fields
                    if 'name' not in proj:
                        warnings.append(f"Project entry {i} missing 'name'")
                    if 'type' not in proj:
                        warnings.append(f"Project entry {i} missing 'type'")
                    elif proj['type'] not in valid_types:
                        warnings.append(f"Project entry {i} has invalid type '{proj['type']}'. Valid types: {', '.join(valid_types)}")
                    if 'description' not in proj:
                        warnings.append(f"Project entry {i} missing 'description'")
                    if 'technologies' not in proj:
                        warnings.append(f"Project entry {i} missing 'technologies'")
                    if 'outcomes' not in proj:
                        warnings.append(f"Project entry {i} missing 'outcomes'")
    
    return warnings


def validate_with_schema(data: Dict[str, Any]) -> List[str]:
    """
    Validate career database against JSON schema.
    
    Args:
        data: Parsed career database dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    schema_path = Path(__file__).parent / "career_database_schema.json"
    
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Validate against schema
        jsonschema.validate(instance=data, schema=schema)
        return []
        
    except jsonschema.exceptions.ValidationError as e:
        # Format validation errors
        errors = []
        if e.path:
            path = " -> ".join(str(p) for p in e.path)
            errors.append(f"Validation error at {path}: {e.message}")
        else:
            errors.append(f"Validation error: {e.message}")
        
        # Check for additional errors
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(data):
            if error != e:  # Avoid duplicate
                if error.path:
                    path = " -> ".join(str(p) for p in error.path)
                    errors.append(f"Validation error at {path}: {error.message}")
                else:
                    errors.append(f"Validation error: {error.message}")
        
        return errors
        
    except FileNotFoundError:
        return ["Schema file not found: career_database_schema.json"]
    except json.JSONDecodeError:
        return ["Invalid JSON schema file"]
    except Exception as e:
        return [f"Schema validation error: {str(e)}"]


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


class CareerDatabaseParser:
    """
    High-level parser for career database files.
    
    This class provides a simple interface for loading and validating
    career databases, handling the enhanced schema with nested projects.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.data = None
        self.warnings = []
        self.errors = []
    
    def parse(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse a career database file or directory.
        
        Args:
            path: Path to YAML file or directory
            
        Returns:
            Parsed career database dictionary
            
        Raises:
            CareerDatabaseError: If parsing fails
        """
        self.data = load_career_database(path)
        self.warnings = validate_career_database(self.data)
        
        # Also validate against schema if available
        schema_errors = validate_with_schema(self.data)
        if schema_errors:
            self.errors.extend(schema_errors)
        
        return self.data
    
    def get_experience_projects(self) -> List[Dict[str, Any]]:
        """
        Extract all projects from experience entries.
        
        Returns:
            List of all projects across all experience entries
        """
        if not self.data or 'experience' not in self.data:
            return []
        
        all_projects = []
        for exp in self.data.get('experience', []):
            if 'projects' in exp and isinstance(exp['projects'], list):
                # Add company context to each project
                for proj in exp['projects']:
                    proj_with_context = proj.copy()
                    proj_with_context['company'] = exp.get('company', 'Unknown')
                    proj_with_context['job_title'] = exp.get('title', 'Unknown')
                    all_projects.append(proj_with_context)
        
        return all_projects
    
    def get_all_technologies(self) -> List[str]:
        """
        Extract all unique technologies from the entire database.
        
        Returns:
            Sorted list of unique technology names
        """
        if not self.data:
            return []
        
        tech_set = set()
        
        # From skills
        if 'skills' in self.data:
            skills = self.data['skills']
            tech_set.update(skills.get('technical', []))
            tech_set.update(skills.get('tools', []))
            tech_set.update(skills.get('frameworks', []))
        
        # From experience
        for exp in self.data.get('experience', []):
            tech_set.update(exp.get('technologies', []))
            # From nested projects
            for proj in exp.get('projects', []):
                tech_set.update(proj.get('technologies', []))
        
        # From standalone projects
        for proj in self.data.get('projects', []):
            tech_set.update(proj.get('technologies', []))
        
        return sorted(list(tech_set))
    
    def get_achievements_by_role(self, role_title: str) -> List[str]:
        """
        Get all achievements for a specific role.
        
        Args:
            role_title: Job title to search for
            
        Returns:
            List of achievements for that role
        """
        if not self.data:
            return []
        
        achievements = []
        for exp in self.data.get('experience', []):
            if role_title.lower() in exp.get('title', '').lower():
                achievements.extend(exp.get('achievements', []))
                # Also get achievements from projects in this role
                for proj in exp.get('projects', []):
                    achievements.extend(proj.get('achievements', []))
        
        return achievements