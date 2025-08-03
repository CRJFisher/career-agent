"""
Database backend abstraction for career database storage.

This module provides an abstract interface for different storage backends
(YAML, SQLite, etc.) and implements concrete backends for each storage type.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for career database storage backends."""
    
    @abstractmethod
    def save(self, data: Dict[str, Any], path: Union[str, Path]) -> bool:
        """Save career database to storage.
        
        Args:
            data: Career database dictionary
            path: Storage path (file path for YAML, db path for SQLite)
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def load(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load career database from storage.
        
        Args:
            path: Storage path
            
        Returns:
            Career database dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if database exists at given path.
        
        Args:
            path: Storage path
            
        Returns:
            True if exists
        """
        pass
    
    @abstractmethod
    def delete(self, path: Union[str, Path]) -> bool:
        """Delete database at given path.
        
        Args:
            path: Storage path
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def backup(self, path: Union[str, Path], backup_path: Union[str, Path]) -> bool:
        """Create a backup of the database.
        
        Args:
            path: Source storage path
            backup_path: Backup destination path
            
        Returns:
            Success status
        """
        pass
    
    # Optional query methods (mainly for SQLite)
    def query_experiences(self, **filters) -> List[Dict[str, Any]]:
        """Query experiences with filters.
        
        Args:
            **filters: Query filters (e.g., company="Google", min_date="2020-01-01")
            
        Returns:
            List of matching experiences
        """
        raise NotImplementedError("Query not supported by this backend")
    
    def query_skills(self, skill_names: List[str]) -> List[Dict[str, Any]]:
        """Query experiences by skills.
        
        Args:
            skill_names: List of skill names to search for
            
        Returns:
            List of experiences with matching skills
        """
        raise NotImplementedError("Query not supported by this backend")
    
    def get_version_history(self, path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Get version history of database changes.
        
        Args:
            path: Storage path
            
        Returns:
            List of version records
        """
        raise NotImplementedError("Version history not supported by this backend")


class YAMLBackend(StorageBackend):
    """YAML file storage backend."""
    
    def __init__(self):
        """Initialize YAML backend."""
        import yaml
        self.yaml = yaml
        
    def save(self, data: Dict[str, Any], path: Union[str, Path]) -> bool:
        """Save career database to YAML file."""
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            data_with_meta = {
                "_metadata": {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "backend": "yaml"
                },
                **data
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data_with_meta, f, 
                              default_flow_style=False, 
                              sort_keys=False,
                              allow_unicode=True)
            
            logger.info(f"Saved career database to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save YAML: {e}")
            return False
    
    def load(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load career database from YAML file."""
        try:
            path = Path(path)
            if not path.exists():
                return None
                
            with open(path, 'r', encoding='utf-8') as f:
                data = self.yaml.safe_load(f)
            
            # Remove metadata before returning
            if "_metadata" in data:
                del data["_metadata"]
                
            return data
            
        except Exception as e:
            logger.error(f"Failed to load YAML: {e}")
            return None
    
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if YAML file exists."""
        return Path(path).exists()
    
    def delete(self, path: Union[str, Path]) -> bool:
        """Delete YAML file."""
        try:
            path = Path(path)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete YAML: {e}")
            return False
    
    def backup(self, path: Union[str, Path], backup_path: Union[str, Path]) -> bool:
        """Create a backup of YAML file."""
        try:
            import shutil
            path = Path(path)
            backup_path = Path(backup_path)
            
            if path.exists():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_path)
                logger.info(f"Created backup at {backup_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False


class SQLiteBackend(StorageBackend):
    """SQLite database storage backend."""
    
    def __init__(self):
        """Initialize SQLite backend."""
        import sqlite3
        self.sqlite3 = sqlite3
        self._connections = {}
    
    def _get_connection(self, path: Union[str, Path]):
        """Get or create database connection."""
        path_str = str(path)
        if path_str not in self._connections:
            self._connections[path_str] = self.sqlite3.connect(path_str)
            self._init_schema(self._connections[path_str])
        return self._connections[path_str]
    
    def _init_schema(self, conn):
        """Initialize database schema."""
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
            -- Metadata table
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Experiences table
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                period TEXT,
                start_date DATE,
                end_date DATE,
                description TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Achievements table
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experience_id INTEGER,
                achievement TEXT,
                FOREIGN KEY (experience_id) REFERENCES experiences(id)
            );
            
            -- Technologies/Skills table
            CREATE TABLE IF NOT EXISTS technologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            );
            
            -- Experience-Technology junction table
            CREATE TABLE IF NOT EXISTS experience_technologies (
                experience_id INTEGER,
                technology_id INTEGER,
                PRIMARY KEY (experience_id, technology_id),
                FOREIGN KEY (experience_id) REFERENCES experiences(id),
                FOREIGN KEY (technology_id) REFERENCES technologies(id)
            );
            
            -- Education table
            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                degree TEXT,
                institution TEXT,
                period TEXT,
                start_date DATE,
                end_date DATE,
                description TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Projects table
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                period TEXT,
                technologies TEXT,
                url TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Skills summary table
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Version history table
            CREATE TABLE IF NOT EXISTS version_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                data_before TEXT,
                data_after TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_experiences_company ON experiences(company);
            CREATE INDEX IF NOT EXISTS idx_experiences_dates ON experiences(start_date, end_date);
            CREATE INDEX IF NOT EXISTS idx_technologies_name ON technologies(name);
        """)
        
        conn.commit()
    
    def save(self, data: Dict[str, Any], path: Union[str, Path]) -> bool:
        """Save career database to SQLite."""
        try:
            conn = self._get_connection(path)
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Clear existing data (we'll do a full replace for now)
            cursor.execute("DELETE FROM experience_technologies")
            cursor.execute("DELETE FROM achievements")
            cursor.execute("DELETE FROM experiences")
            cursor.execute("DELETE FROM education")
            cursor.execute("DELETE FROM projects")
            cursor.execute("DELETE FROM skills")
            
            # Save experiences
            if "experiences" in data:
                for exp in data["experiences"]:
                    cursor.execute("""
                        INSERT INTO experiences 
                        (title, company, location, period, description, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        exp.get("title"),
                        exp.get("company"),
                        exp.get("location"),
                        exp.get("period"),
                        exp.get("description"),
                        json.dumps(exp)
                    ))
                    
                    exp_id = cursor.lastrowid
                    
                    # Save achievements
                    for achievement in exp.get("achievements", []):
                        cursor.execute("""
                            INSERT INTO achievements (experience_id, achievement)
                            VALUES (?, ?)
                        """, (exp_id, achievement))
                    
                    # Save technologies
                    for tech in exp.get("technologies", []):
                        # Insert or get technology
                        cursor.execute("""
                            INSERT OR IGNORE INTO technologies (name) VALUES (?)
                        """, (tech,))
                        
                        cursor.execute("""
                            SELECT id FROM technologies WHERE name = ?
                        """, (tech,))
                        tech_id = cursor.fetchone()[0]
                        
                        # Link to experience
                        cursor.execute("""
                            INSERT INTO experience_technologies 
                            (experience_id, technology_id) VALUES (?, ?)
                        """, (exp_id, tech_id))
            
            # Save education
            if "education" in data:
                for edu in data["education"]:
                    cursor.execute("""
                        INSERT INTO education 
                        (degree, institution, period, description, raw_data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        edu.get("degree"),
                        edu.get("institution"),
                        edu.get("period"),
                        edu.get("description"),
                        json.dumps(edu)
                    ))
            
            # Save projects
            if "projects" in data:
                for proj in data["projects"]:
                    cursor.execute("""
                        INSERT INTO projects 
                        (name, description, period, technologies, url, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        proj.get("name"),
                        proj.get("description"),
                        proj.get("period"),
                        json.dumps(proj.get("technologies", [])),
                        proj.get("url"),
                        json.dumps(proj)
                    ))
            
            # Save skills
            if "skills" in data:
                for category, skills in data["skills"].items():
                    cursor.execute("""
                        INSERT INTO skills (category, skills)
                        VALUES (?, ?)
                    """, (category, json.dumps(skills)))
            
            # Update metadata
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('last_updated', ?)
            """, (datetime.now().isoformat(),))
            
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('version', '1.0')
            """)
            
            # Commit transaction
            conn.commit()
            logger.info(f"Saved career database to SQLite: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to SQLite: {e}")
            if conn:
                conn.rollback()
            return False
    
    def load(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load career database from SQLite."""
        try:
            if not self.exists(path):
                return None
                
            conn = self._get_connection(path)
            cursor = conn.cursor()
            
            data = {}
            
            # Load experiences
            cursor.execute("""
                SELECT id, title, company, location, period, description, raw_data
                FROM experiences
                ORDER BY id
            """)
            
            experiences = []
            for row in cursor.fetchall():
                exp_id = row[0]
                
                # Try to use raw_data first, fallback to individual fields
                if row[6]:
                    exp = json.loads(row[6])
                else:
                    exp = {
                        "title": row[1],
                        "company": row[2],
                        "location": row[3],
                        "period": row[4],
                        "description": row[5]
                    }
                
                # Load achievements
                cursor.execute("""
                    SELECT achievement FROM achievements
                    WHERE experience_id = ?
                """, (exp_id,))
                exp["achievements"] = [r[0] for r in cursor.fetchall()]
                
                # Load technologies
                cursor.execute("""
                    SELECT t.name FROM technologies t
                    JOIN experience_technologies et ON t.id = et.technology_id
                    WHERE et.experience_id = ?
                """, (exp_id,))
                exp["technologies"] = [r[0] for r in cursor.fetchall()]
                
                experiences.append(exp)
            
            if experiences:
                data["experiences"] = experiences
            
            # Load education
            cursor.execute("""
                SELECT degree, institution, period, description, raw_data
                FROM education
                ORDER BY id
            """)
            
            education = []
            for row in cursor.fetchall():
                if row[4]:
                    edu = json.loads(row[4])
                else:
                    edu = {
                        "degree": row[0],
                        "institution": row[1],
                        "period": row[2],
                        "description": row[3]
                    }
                education.append(edu)
            
            if education:
                data["education"] = education
            
            # Load projects
            cursor.execute("""
                SELECT name, description, period, technologies, url, raw_data
                FROM projects
                ORDER BY id
            """)
            
            projects = []
            for row in cursor.fetchall():
                if row[5]:
                    proj = json.loads(row[5])
                else:
                    proj = {
                        "name": row[0],
                        "description": row[1],
                        "period": row[2],
                        "technologies": json.loads(row[3]) if row[3] else [],
                        "url": row[4]
                    }
                projects.append(proj)
            
            if projects:
                data["projects"] = projects
            
            # Load skills
            cursor.execute("""
                SELECT category, skills FROM skills
            """)
            
            skills = {}
            for row in cursor.fetchall():
                skills[row[0]] = json.loads(row[1])
            
            if skills:
                data["skills"] = skills
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load from SQLite: {e}")
            return None
    
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if SQLite database exists."""
        return Path(path).exists()
    
    def delete(self, path: Union[str, Path]) -> bool:
        """Delete SQLite database."""
        try:
            path = Path(path)
            path_str = str(path)
            
            # Close connection if open
            if path_str in self._connections:
                self._connections[path_str].close()
                del self._connections[path_str]
            
            # Delete file
            if path.exists():
                path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete SQLite database: {e}")
            return False
    
    def backup(self, path: Union[str, Path], backup_path: Union[str, Path]) -> bool:
        """Create a backup of SQLite database."""
        try:
            import shutil
            path = Path(path)
            backup_path = Path(backup_path)
            
            # Close connection if open
            path_str = str(path)
            if path_str in self._connections:
                self._connections[path_str].close()
                del self._connections[path_str]
            
            if path.exists():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_path)
                logger.info(f"Created SQLite backup at {backup_path}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to create SQLite backup: {e}")
            return False
    
    def query_experiences(self, **filters) -> List[Dict[str, Any]]:
        """Query experiences with filters."""
        # This would be implemented with SQL queries based on filters
        # For now, returning empty list
        return []
    
    def query_skills(self, skill_names: List[str]) -> List[Dict[str, Any]]:
        """Query experiences by skills."""
        # This would search for experiences with matching technologies
        # For now, returning empty list
        return []
    
    def __del__(self):
        """Close all connections on cleanup."""
        for conn in self._connections.values():
            conn.close()


# Factory function
def get_storage_backend(backend_type: str = "yaml") -> StorageBackend:
    """Get storage backend instance.
    
    Args:
        backend_type: Type of backend ("yaml" or "sqlite")
        
    Returns:
        Storage backend instance
        
    Raises:
        ValueError: If backend type is not supported
    """
    if backend_type.lower() == "yaml":
        return YAMLBackend()
    elif backend_type.lower() == "sqlite":
        return SQLiteBackend()
    else:
        raise ValueError(f"Unsupported backend type: {backend_type}")