"""Tests for SQLite database backend."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from utils.database_backend import SQLiteBackend, YAMLBackend, get_storage_backend
from utils.database_migration import DatabaseMigrator


class TestSQLiteBackend:
    """Test suite for SQLite backend."""
    
    @pytest.fixture
    def sqlite_backend(self):
        """Create SQLite backend instance."""
        return SQLiteBackend()
    
    @pytest.fixture
    def yaml_backend(self):
        """Create YAML backend instance."""
        return YAMLBackend()
    
    @pytest.fixture
    def sample_data(self):
        """Sample career database data."""
        return {
            "experiences": [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "location": "San Francisco, CA",
                    "period": "2020-2023",
                    "description": "Led development of microservices",
                    "achievements": [
                        "Reduced latency by 50%",
                        "Mentored 5 junior developers"
                    ],
                    "technologies": ["Python", "Docker", "Kubernetes"]
                },
                {
                    "title": "Software Engineer",
                    "company": "StartupXYZ",
                    "location": "Remote",
                    "period": "2018-2020",
                    "description": "Full-stack development",
                    "achievements": [
                        "Built MVP in 3 months",
                        "Scaled to 10k users"
                    ],
                    "technologies": ["React", "Node.js", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "University of Example",
                    "period": "2014-2018",
                    "description": "Focus on distributed systems"
                }
            ],
            "projects": [
                {
                    "name": "OpenSourceProject",
                    "description": "A tool for developers",
                    "period": "2021-present",
                    "technologies": ["Go", "gRPC"],
                    "url": "https://github.com/example/project"
                }
            ],
            "skills": {
                "languages": ["Python", "JavaScript", "Go"],
                "frameworks": ["Django", "React", "FastAPI"],
                "tools": ["Git", "Docker", "Jenkins"]
            }
        }
    
    def test_save_and_load(self, sqlite_backend, sample_data):
        """Test saving and loading data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Save data
            assert sqlite_backend.save(sample_data, db_path)
            assert db_path.exists()
            
            # Load data
            loaded_data = sqlite_backend.load(db_path)
            assert loaded_data is not None
            
            # Verify structure
            assert "experiences" in loaded_data
            assert len(loaded_data["experiences"]) == 2
            assert loaded_data["experiences"][0]["title"] == "Senior Software Engineer"
            
            # Verify achievements
            assert len(loaded_data["experiences"][0]["achievements"]) == 2
            
            # Verify technologies
            assert "Python" in loaded_data["experiences"][0]["technologies"]
            
            # Verify education
            assert "education" in loaded_data
            assert len(loaded_data["education"]) == 1
            
            # Verify skills
            assert "skills" in loaded_data
            assert "languages" in loaded_data["skills"]
            assert "Python" in loaded_data["skills"]["languages"]
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_exists(self, sqlite_backend):
        """Test database existence check."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Should exist (empty file created)
            assert sqlite_backend.exists(db_path)
            
            # Delete and check
            db_path.unlink()
            assert not sqlite_backend.exists(db_path)
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_delete(self, sqlite_backend, sample_data):
        """Test database deletion."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Save data
            sqlite_backend.save(sample_data, db_path)
            assert db_path.exists()
            
            # Delete
            assert sqlite_backend.delete(db_path)
            assert not db_path.exists()
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_backup(self, sqlite_backend, sample_data):
        """Test database backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            backup_path = Path(tmpdir) / "backup.db"
            
            # Save data
            sqlite_backend.save(sample_data, db_path)
            
            # Create backup
            assert sqlite_backend.backup(db_path, backup_path)
            assert backup_path.exists()
            
            # Verify backup content
            backup_data = sqlite_backend.load(backup_path)
            assert backup_data == sample_data
    
    def test_empty_database(self, sqlite_backend):
        """Test handling of empty database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Save empty data
            empty_data = {}
            assert sqlite_backend.save(empty_data, db_path)
            
            # Load should return empty dict
            loaded = sqlite_backend.load(db_path)
            assert loaded == {}
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_special_characters(self, sqlite_backend):
        """Test handling of special characters."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            # Data with special characters
            data = {
                "experiences": [{
                    "title": "Software Engineer (Senior)",
                    "company": "Company & Co.",
                    "description": "Worked on 'special' projects with \"quotes\"",
                    "achievements": ["100% test coverage", "Used C++ and C#"],
                    "technologies": ["C++", "C#", "Node.js"]
                }]
            }
            
            # Save and load
            assert sqlite_backend.save(data, db_path)
            loaded = sqlite_backend.load(db_path)
            
            # Verify special characters preserved
            exp = loaded["experiences"][0]
            assert exp["title"] == "Software Engineer (Senior)"
            assert exp["company"] == "Company & Co."
            assert "quotes" in exp["description"]
            assert "100%" in exp["achievements"][0]
            
        finally:
            if db_path.exists():
                db_path.unlink()


class TestDatabaseMigration:
    """Test suite for database migration."""
    
    @pytest.fixture
    def migrator(self):
        """Create database migrator."""
        return DatabaseMigrator()
    
    @pytest.fixture
    def sample_data(self):
        """Sample career database data."""
        return {
            "experiences": [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "location": "San Francisco, CA",
                    "period": "2020-2023",
                    "description": "Led development of microservices",
                    "achievements": [
                        "Reduced latency by 50%",
                        "Mentored 5 junior developers"
                    ],
                    "technologies": ["Python", "Docker", "Kubernetes"]
                },
                {
                    "title": "Software Engineer",
                    "company": "StartupXYZ",
                    "location": "Remote",
                    "period": "2018-2020",
                    "description": "Full-stack development",
                    "achievements": [
                        "Built MVP in 3 months",
                        "Scaled to 10k users"
                    ],
                    "technologies": ["React", "Node.js", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "University of Example",
                    "period": "2014-2018",
                    "description": "Focus on distributed systems"
                }
            ],
            "projects": [
                {
                    "name": "OpenSourceProject",
                    "description": "A tool for developers",
                    "period": "2021-present",
                    "technologies": ["Go", "gRPC"],
                    "url": "https://github.com/example/project"
                }
            ],
            "skills": {
                "languages": ["Python", "JavaScript", "Go"],
                "frameworks": ["Django", "React", "FastAPI"],
                "tools": ["Git", "Docker", "Jenkins"]
            }
        }
    
    def test_yaml_to_sqlite_migration(self, migrator, sample_data):
        """Test migrating from YAML to SQLite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test.yaml"
            sqlite_path = Path(tmpdir) / "test.db"
            
            # Save to YAML
            yaml_backend = YAMLBackend()
            yaml_backend.save(sample_data, yaml_path)
            
            # Migrate to SQLite
            assert migrator.migrate(
                yaml_path, "yaml",
                sqlite_path, "sqlite",
                backup=False
            )
            
            # Verify SQLite has same data
            sqlite_backend = SQLiteBackend()
            sqlite_data = sqlite_backend.load(sqlite_path)
            
            # Compare key structures
            assert set(sqlite_data.keys()) == set(sample_data.keys())
            assert len(sqlite_data["experiences"]) == len(sample_data["experiences"])
            assert sqlite_data["experiences"][0]["title"] == sample_data["experiences"][0]["title"]
    
    def test_sqlite_to_yaml_migration(self, migrator, sample_data):
        """Test migrating from SQLite to YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "test.db"
            yaml_path = Path(tmpdir) / "test.yaml"
            
            # Save to SQLite
            sqlite_backend = SQLiteBackend()
            sqlite_backend.save(sample_data, sqlite_path)
            
            # Migrate to YAML
            assert migrator.migrate(
                sqlite_path, "sqlite",
                yaml_path, "yaml",
                backup=False
            )
            
            # Verify YAML has same data
            yaml_backend = YAMLBackend()
            yaml_data = yaml_backend.load(yaml_path)
            
            # Compare
            assert yaml_data == sample_data
    
    def test_migration_with_backup(self, migrator, sample_data):
        """Test migration creates backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test.yaml"
            sqlite_path = Path(tmpdir) / "test.db"
            
            # Save to YAML
            yaml_backend = YAMLBackend()
            yaml_backend.save(sample_data, yaml_path)
            
            # Migrate with backup
            assert migrator.migrate(
                yaml_path, "yaml",
                sqlite_path, "sqlite",
                backup=True
            )
            
            # Check backup was created
            backup_files = list(Path(tmpdir).glob("test_backup_*.yaml"))
            assert len(backup_files) == 1
    
    def test_migration_overwrites_existing(self, migrator, sample_data):
        """Test migration handles existing destination."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test.yaml"
            sqlite_path = Path(tmpdir) / "test.db"
            
            # Save to both
            yaml_backend = YAMLBackend()
            sqlite_backend = SQLiteBackend()
            
            yaml_backend.save(sample_data, yaml_path)
            
            # Save different data to SQLite
            different_data = {"experiences": [{"title": "Different Job"}]}
            sqlite_backend.save(different_data, sqlite_path)
            
            # Migrate should overwrite
            assert migrator.migrate(
                yaml_path, "yaml",
                sqlite_path, "sqlite",
                backup=True
            )
            
            # Verify SQLite has YAML data
            result = sqlite_backend.load(sqlite_path)
            assert len(result["experiences"]) == 2
            assert result["experiences"][0]["title"] == "Senior Software Engineer"


class TestStorageFactory:
    """Test storage backend factory."""
    
    def test_get_yaml_backend(self):
        """Test getting YAML backend."""
        backend = get_storage_backend("yaml")
        assert isinstance(backend, YAMLBackend)
    
    def test_get_sqlite_backend(self):
        """Test getting SQLite backend."""
        backend = get_storage_backend("sqlite")
        assert isinstance(backend, SQLiteBackend)
    
    def test_invalid_backend(self):
        """Test invalid backend type."""
        with pytest.raises(ValueError):
            get_storage_backend("invalid")