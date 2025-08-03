# SQLite Database Backend

The Career Application Agent now supports SQLite as an alternative to YAML for storing career data. This provides better performance for large databases and enables advanced querying capabilities.

## Features

- **Dual Backend Support**: Switch between YAML and SQLite backends seamlessly
- **Automatic Migration**: Convert existing YAML databases to SQLite with a single command
- **Backward Compatibility**: Existing code continues to work without modification
- **Performance**: Faster queries for large career databases
- **Structured Storage**: Normalized database schema for efficient data storage

## Database Schema

The SQLite backend uses a normalized schema with the following tables:

### Core Tables
- `experiences`: Work experience records
- `education`: Educational background
- `skills`: Technical and soft skills
- `projects`: Personal and professional projects
- `certifications`: Professional certifications
- `publications`: Published works
- `awards`: Awards and recognitions

### Relationship Tables
- `experience_achievements`: Achievements linked to experiences
- `experience_technologies`: Technologies used in experiences
- `experience_projects`: Projects within work experiences
- `project_technologies`: Technologies used in projects
- `project_outcomes`: Project outcomes and results

## Usage

### Checking Current Backend

```bash
# Show current database backend configuration
python main.py --db-info

# Show just the current backend type
python main.py --db-backend
```

### Switching Backends

```bash
# Migrate from YAML to SQLite
python main.py --migrate-db --db-backend sqlite

# Migrate from SQLite to YAML
python main.py --migrate-db --db-backend yaml
```

### Using SQLite Backend in Code

```python
from utils.database_parser_v2 import CareerDatabaseParser

# Auto-detects backend from file extension
parser = CareerDatabaseParser()
career_data = parser.load("career_database.db")  # SQLite
career_data = parser.load("career_database.yaml")  # YAML

# Explicitly specify backend
parser = CareerDatabaseParser(backend_type="sqlite")
career_data = parser.load("my_database.db")

# Save to SQLite
parser.save(career_data, "career_database.db")
```

### Environment Variables

You can set the default backend using environment variables:

```bash
export CAREER_DB_BACKEND=sqlite
python main.py --build-db
```

## Configuration

The database backend configuration is stored in `~/.career-agent/config.json`:

```json
{
  "database": {
    "backend": "sqlite",
    "yaml_path": "~/.career-agent/career_database.yaml",
    "sqlite_path": "~/.career-agent/career_database.db"
  }
}
```

## Migration Process

The migration process:
1. Creates a backup of the existing database (with timestamp)
2. Reads all data from the source backend
3. Converts data to the target backend format
4. Writes data to the new backend
5. Verifies the migration was successful

### Migration Examples

```bash
# Migrate with automatic backup
python main.py --migrate-db --db-backend sqlite

# The backup will be created as:
# career_database_backup_20240115_143022.yaml
```

## Performance Considerations

### When to Use SQLite

- Large career databases (100+ experiences)
- Need for complex queries (e.g., find all Java projects in 2020-2023)
- Multiple users accessing the same database
- Integration with other tools that support SQLite

### When to Use YAML

- Small career databases (< 50 experiences)
- Need for manual editing in text editor
- Simple version control with Git
- Maximum portability

## Advanced Queries

With SQLite backend, you can perform advanced queries:

```python
from utils.database_backend import SQLiteBackend

backend = SQLiteBackend()
backend.load("career_database.db")

# Query experiences by company
experiences = backend.query_experiences(company="TechCorp")

# Query experiences with specific technology
java_experiences = backend.query_experiences(technology="Java")

# Query experiences in date range
recent_exp = backend.query_experiences(
    start_date="2020-01-01", 
    end_date="2023-12-31"
)
```

## Troubleshooting

### Common Issues

1. **Migration fails with "Database locked" error**
   - Ensure no other process is accessing the database
   - Close any SQLite viewers or editors

2. **Data appears missing after migration**
   - Check the backup file was created successfully
   - Verify the correct paths in config.json
   - Run validation: `python main.py --validate-db`

3. **Performance is slower with SQLite**
   - Run `VACUUM` on the database: `sqlite3 career_database.db "VACUUM;"`
   - Ensure the database file is on local storage (not network drive)

### Debugging

Enable debug logging to see detailed migration information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

### CareerDatabaseParser

```python
class CareerDatabaseParser:
    def __init__(self, backend_type: Optional[str] = None):
        """Initialize parser with specified backend."""
        
    def load(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load career database from file."""
        
    def save(self, data: Dict[str, Any], path: Union[str, Path]) -> bool:
        """Save career database to file."""
        
    def query_experiences(self, path: Union[str, Path], **filters) -> List[Dict[str, Any]]:
        """Query experiences with filters (SQLite only)."""
```

### DatabaseConfig

```python
from config import get_database_config

config = get_database_config()

# Get current backend
backend = config.backend_type

# Switch backend
config.switch_backend("sqlite", migrate_data=True)

# Get database paths
paths = config.get_all_paths()
```

## Future Enhancements

- Full-text search capabilities
- Export to multiple formats (JSON, CSV)
- Database merging from multiple sources
- Incremental synchronization
- Web-based database editor