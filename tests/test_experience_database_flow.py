"""Unit tests for ExperienceDatabaseFlow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import yaml

from flow import ExperienceDatabaseFlow

# Mock the nodes to avoid LLM initialization
from unittest.mock import MagicMock
def mock_node():
    node = MagicMock()
    node.successors = {}
    node.next = MagicMock(return_value=node)
    node.__rshift__ = MagicMock(return_value=node)
    return node


class TestExperienceDatabaseFlow:
    """Test suite for ExperienceDatabaseFlow."""
    
    @pytest.fixture
    def basic_config(self):
        """Basic flow configuration."""
        return {
            "scan_config": {
                "local_directories": ["/test/docs"],
                "file_types": [".pdf", ".md"]
            },
            "output_path": "test_career_db.yaml",
            "enable_checkpoints": False  # Disable for simpler testing
        }
    
    @pytest.fixture
    def flow(self, basic_config):
        """Create flow instance with basic config."""
        with patch('flow.ScanDocumentsNode', return_value=mock_node()):
            with patch('flow.ExtractExperienceNode', return_value=mock_node()):
                with patch('flow.BuildDatabaseNode', return_value=mock_node()):
                    with patch('flow.SaveCheckpointNode', return_value=mock_node()):
                        return ExperienceDatabaseFlow(basic_config)
    
    def test_init_without_checkpoints(self, basic_config):
        """Test flow initialization without checkpoints."""
        with patch('flow.ScanDocumentsNode', return_value=mock_node()):
            with patch('flow.ExtractExperienceNode', return_value=mock_node()):
                with patch('flow.BuildDatabaseNode', return_value=mock_node()):
                    flow = ExperienceDatabaseFlow(basic_config)
        
        assert flow.config == basic_config
        assert not flow.checkpoints_enabled
        assert flow.start_node is not None
        # Should have direct connections without checkpoint nodes
    
    def test_init_with_checkpoints(self):
        """Test flow initialization with checkpoints enabled."""
        config = {
            "enable_checkpoints": True,
            "checkpoint_dir": ".test_checkpoints"
        }
        with patch('flow.ScanDocumentsNode', return_value=mock_node()):
            with patch('flow.ExtractExperienceNode', return_value=mock_node()):
                with patch('flow.BuildDatabaseNode', return_value=mock_node()):
                    with patch('flow.SaveCheckpointNode', return_value=mock_node()):
                        flow = ExperienceDatabaseFlow(config)
        
        assert flow.checkpoints_enabled
        assert flow.checkpoint_dir == ".test_checkpoints"
        # Flow should include checkpoint nodes
    
    def test_prep_sets_configuration(self, flow):
        """Test prep method sets up configuration correctly."""
        shared = {}
        
        result = flow.prep(shared)
        
        # Check configuration was applied
        assert "scan_config" in shared
        assert shared["scan_config"]["local_directories"] == ["/test/docs"]
        assert shared["database_output_path"] == "test_career_db.yaml"
        assert shared["merge_strategy"] == "smart"  # Default
        assert result["flow_initialized"] is True
    
    @patch('utils.database_parser.load_career_database')
    def test_prep_loads_existing_database(self, mock_load, flow):
        """Test prep loads existing database when present."""
        # Mock existing database
        mock_load.return_value = {"personal_info": {"name": "John Doe"}}
        
        with patch('pathlib.Path.exists', return_value=True):
            shared = {}
            flow.prep(shared)
            
            assert "existing_career_database" in shared
            assert shared["existing_career_database"]["personal_info"]["name"] == "John Doe"
    
    def test_prep_initializes_progress_tracking(self, flow):
        """Test prep initializes progress tracking."""
        shared = {}
        
        flow.prep(shared)
        
        assert "flow_progress" in shared
        assert "scanning" in shared["flow_progress"]
        assert "extracting" in shared["flow_progress"]
        assert "building" in shared["flow_progress"]
        assert all(p["status"] == "pending" for p in shared["flow_progress"].values())
    
    def test_count_sources(self, flow):
        """Test document source counting."""
        documents = [
            {"source": "local", "name": "doc1.pdf"},
            {"source": "local", "name": "doc2.pdf"},
            {"source": "google_drive", "name": "doc3.pdf"},
            {"source": "local", "name": "doc4.md"}
        ]
        
        result = flow._count_sources(documents)
        
        assert result["local"] == 3
        assert result["google_drive"] == 1
    
    def test_generate_next_steps_complete(self, flow):
        """Test next steps generation for complete extraction."""
        summary = {
            "extraction_phase": {"failed_extractions": 0},
            "building_phase": {
                "validation_errors": 0,
                "experiences_after_dedup": 5
            },
            "data_completeness": {
                "has_email": True,
                "has_skills": True
            }
        }
        
        next_steps = flow._generate_next_steps(summary)
        
        # Should always include review steps
        assert any("Review extracted experiences" in step for step in next_steps)
        assert any("Run job application flows" in step for step in next_steps)
        # Should not include fix steps
        assert not any("Fix validation errors" in step for step in next_steps)
    
    def test_generate_next_steps_with_issues(self, flow):
        """Test next steps generation with issues."""
        summary = {
            "extraction_phase": {"failed_extractions": 2},
            "building_phase": {"validation_errors": 3},
            "data_completeness": {
                "has_email": False,
                "has_skills": False
            }
        }
        
        next_steps = flow._generate_next_steps(summary)
        
        assert any("failed document extractions" in step for step in next_steps)
        assert any("Fix validation errors" in step for step in next_steps)
        assert any("Add email address" in step for step in next_steps)
        assert any("Add technical skills" in step for step in next_steps)
    
    def test_generate_summary_report(self, flow):
        """Test summary report generation."""
        shared = {
            "document_sources": [
                {"name": "doc1.pdf", "size": 1024000, "source": "local"},
                {"name": "doc2.md", "size": 512000, "source": "local"}
            ],
            "extraction_summary": {
                "total_documents": 2,
                "successful_extractions": 2,
                "failed_extractions": 0,
                "average_confidence": 0.85
            },
            "build_summary": {
                "experiences_extracted": 5,
                "experiences_after_dedup": 3,
                "companies": [{"name": "Tech Corp"}],
                "technologies_found": ["Python", "AWS"],
                "validation_errors": [],
                "extraction_quality": {
                    "high_confidence": 2,
                    "medium_confidence": 0,
                    "low_confidence": 0
                },
                "data_completeness": {
                    "has_email": True,
                    "has_experience": True,
                    "has_skills": True
                }
            }
        }
        
        summary = flow._generate_summary_report(shared, 300)  # 5 minutes
        
        assert summary["flow_status"] == "completed"
        assert summary["duration_minutes"] == 5.0
        assert summary["scanning_phase"]["documents_found"] == 2
        assert summary["scanning_phase"]["total_size_mb"] == 1.5
        assert summary["extraction_phase"]["successful_extractions"] == 2
        assert summary["building_phase"]["experiences_after_dedup"] == 3
        assert summary["quality_metrics"]["high_confidence"] == 2
        assert "next_steps" in summary
    
    @patch('flow.logger')
    def test_log_summary(self, mock_logger, flow):
        """Test summary logging."""
        summary = {
            "duration_minutes": 5.0,
            "scanning_phase": {
                "documents_found": 10,
                "total_size_mb": 25.5,
                "sources": {"local": 8, "google_drive": 2}
            },
            "extraction_phase": {
                "documents_processed": 10,
                "successful_extractions": 9,
                "failed_extractions": 1,
                "average_confidence": 0.82
            },
            "building_phase": {
                "experiences_before_dedup": 15,
                "experiences_after_dedup": 10,
                "companies": 5,
                "technologies_found": 20,
                "database_saved": "career_db.yaml"
            },
            "next_steps": ["Review experiences", "Fix validation errors"]
        }
        
        flow._log_summary(summary)
        
        # Should log all major sections
        assert any("EXPERIENCE DATABASE FLOW COMPLETE" in str(call) for call in mock_logger.info.call_args_list)
        assert any("Duration: 5.0 minutes" in str(call) for call in mock_logger.info.call_args_list)
        assert any("Documents found: 10" in str(call) for call in mock_logger.info.call_args_list)
        assert any("Successful: 9" in str(call) for call in mock_logger.info.call_args_list)
        assert any("Experiences (final): 10" in str(call) for call in mock_logger.info.call_args_list)
    
    @patch('builtins.open', create=True)
    @patch('yaml.dump')
    def test_save_summary(self, mock_yaml_dump, mock_open, flow):
        """Test summary saving to file."""
        summary = {"flow_status": "completed", "duration_minutes": 5.0}
        
        flow._save_summary(summary)
        
        # Should create summaries directory
        mock_open.assert_called()
        mock_yaml_dump.assert_called_once()
        
        # Check YAML dump was called with correct data
        call_args = mock_yaml_dump.call_args
        assert call_args[0][0] == summary
        assert call_args[1]["default_flow_style"] is False
    
    def test_post_generates_complete_report(self, flow):
        """Test post method generates and stores complete report."""
        shared = {
            "document_sources": [{"name": "test.pdf", "size": 1024}],
            "extraction_summary": {
                "total_documents": 1,
                "successful_extractions": 1,
                "failed_extractions": 0,
                "average_confidence": 0.9
            },
            "build_summary": {
                "experiences_after_dedup": 2,
                "companies": [],
                "technologies_found": [],
                "validation_errors": []
            }
        }
        
        # Set start time to a non-zero value to avoid the conditional
        flow.start_time = 100  # Start at t=100
        with patch('time.time', return_value=400):  # End at t=400, so duration = 300s = 5min
            with patch.object(flow, '_save_summary'):
                result = flow.post(shared, {}, None)
        
        assert result == "complete"
        assert "flow_summary" in shared
        assert shared["flow_summary"]["duration_minutes"] == 5.0
    
    def test_find_latest_checkpoint(self, flow):
        """Test finding latest checkpoint file."""
        # Create mock checkpoint files
        checkpoint_dir = Path(".test_checkpoints/experience_db")
        
        with patch.object(Path, 'glob') as mock_glob:
            # Mock checkpoint files with different timestamps
            mock_files = [
                Mock(stem="checkpoint_1", stat=Mock(return_value=Mock(st_mtime=1000))),
                Mock(stem="checkpoint_2", stat=Mock(return_value=Mock(st_mtime=2000))),
                Mock(stem="checkpoint_3", stat=Mock(return_value=Mock(st_mtime=1500)))
            ]
            mock_glob.return_value = mock_files
            
            result = flow._find_latest_checkpoint(checkpoint_dir)
            
            assert result == "checkpoint_2"  # Has highest mtime
    
    def test_find_latest_checkpoint_empty(self, flow):
        """Test finding latest checkpoint when none exist."""
        checkpoint_dir = Path(".test_checkpoints/experience_db")
        
        with patch.object(Path, 'glob', return_value=[]):
            result = flow._find_latest_checkpoint(checkpoint_dir)
            
            assert result is None