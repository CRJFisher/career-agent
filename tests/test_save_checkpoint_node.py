"""Unit tests for SaveCheckpointNode."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import yaml
from datetime import datetime

from nodes import SaveCheckpointNode


class TestSaveCheckpointNode:
    """Test suite for SaveCheckpointNode."""
    
    @pytest.fixture
    def node(self):
        """Create SaveCheckpointNode instance."""
        return SaveCheckpointNode()
    
    @pytest.fixture
    def shared_data(self):
        """Sample shared store data."""
        return {
            "flow_name": "analysis",
            "requirements": {"REQ001": "Python experience"},
            "requirement_mapping_final": {
                "REQ001": {
                    "requirement": "Python experience",
                    "evidence": ["5 years Python development"],
                    "strength": "HIGH"
                }
            },
            "gaps": ["Cloud experience"],
            "coverage_score": 85,
            "flow_config": {"mode": "comprehensive"},
            "flow_progress": {"analysis": "complete"}
        }
    
    def test_init(self, node):
        """Test node initialization."""
        assert node.checkpoint_dir == Path("checkpoints")
        assert node.output_dir == Path("outputs")
        assert node.max_retries == 3
        assert node.wait == 1.0
    
    def test_prep_with_explicit_params(self, node):
        """Test prep with explicit parameters."""
        node.set_params({
            "flow_name": "custom_flow",
            "checkpoint_name": "test_checkpoint",
            "checkpoint_data": ["field1", "field2"],
            "output_file": "custom_output.yaml",
            "user_message": "Custom instructions"
        })
        
        result = node.prep({})
        
        assert result["flow_name"] == "custom_flow"
        assert result["checkpoint_name"] == "test_checkpoint"
        assert result["checkpoint_data"] == ["field1", "field2"]
        assert result["output_file"] == "custom_output.yaml"
        assert result["user_message"] == "Custom instructions"
        assert result["node_class"] == "SaveCheckpointNode"
        assert result["format_version"] == "1.0"
        assert isinstance(result["timestamp"], datetime)
    
    def test_prep_with_flow_defaults(self, node):
        """Test prep with flow-specific defaults."""
        # Test analysis flow
        node.set_params({"flow_name": "analysis"})
        result = node.prep({})
        
        expected_fields = [
            "requirements",
            "requirement_mapping_raw",
            "requirement_mapping_assessed", 
            "requirement_mapping_final",
            "gaps",
            "coverage_score"
        ]
        assert result["checkpoint_data"] == expected_fields
        
        # Test narrative flow
        node.set_params({"flow_name": "narrative"})
        result = node.prep({})
        
        expected_fields = [
            "prioritized_experiences",
            "narrative_strategy",
            "suitability_assessment",
            "requirements",
            "job_title",
            "company_name"
        ]
        assert result["checkpoint_data"] == expected_fields
        
        # Test experience_db flow
        node.set_params({"flow_name": "experience_db"})
        result = node.prep({})
        
        expected_fields = [
            "document_sources",
            "extracted_experiences",
            "extraction_summary"
        ]
        assert result["checkpoint_data"] == expected_fields
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('shutil.copy2')
    def test_exec_creates_directories(self, mock_copy, mock_exists, mock_mkdir, node):
        """Test exec creates necessary directories."""
        config = {
            "flow_name": "test_flow",
            "checkpoint_name": "test_checkpoint",
            "timestamp": datetime.now(),
            "output_file": "test_output.yaml"
        }
        
        mock_exists.return_value = False
        
        result = node.exec(config)
        
        # Check directories were created
        assert mock_mkdir.call_count >= 2
        
        # Check result structure
        assert "checkpoint_path" in result
        assert "output_path" in result
        assert "latest_link" in result
        assert result["checkpoint_path"].name.startswith("test_checkpoint_")
        assert result["output_path"].name == "test_output.yaml"
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.resolve')
    @patch('shutil.copy2')
    def test_exec_backs_up_existing_checkpoint(self, mock_copy, mock_resolve, mock_exists, mock_mkdir, node):
        """Test exec backs up existing checkpoint."""
        config = {
            "flow_name": "test_flow",
            "checkpoint_name": "test_checkpoint",
            "timestamp": datetime.now(),
            "output_file": "test_output.yaml"
        }
        
        # Mock existing checkpoint
        mock_exists.return_value = True
        mock_resolve.return_value = Path("/fake/checkpoint.yaml")
        
        result = node.exec(config)
        
        # Check backup was attempted
        mock_copy.assert_called_once()
        backup_call = mock_copy.call_args[0]
        assert str(backup_call[1]).endswith('.yaml.bak')
    
    @patch('yaml.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.symlink_to')
    def test_post_saves_checkpoint(self, mock_symlink, mock_unlink, mock_exists, mock_mkdir, mock_file, mock_yaml_dump, node, shared_data):
        """Test post saves checkpoint file correctly."""
        prep_res = {
            "flow_name": "analysis",
            "checkpoint_name": "test",
            "checkpoint_data": ["requirements", "gaps"]
        }
        
        exec_res = {
            "checkpoint_path": Path("checkpoints/analysis/test_20240101_120000.yaml"),
            "output_path": Path("outputs/test_output.yaml"),
            "latest_link": Path("checkpoints/analysis/test_latest.yaml"),
            "config": {
                "flow_name": "analysis",
                "checkpoint_name": "test",
                "timestamp": datetime.now(),
                "checkpoint_data": ["requirements", "gaps"],
                "user_message": None,
                "node_class": "SaveCheckpointNode",
                "format_version": "1.0"
            }
        }
        
        mock_exists.return_value = False
        
        result = node.post(shared_data, prep_res, exec_res)
        
        # Check files were written
        assert mock_file.call_count == 2  # checkpoint + output
        
        # Verify yaml.dump was called twice (checkpoint + output)
        assert mock_yaml_dump.call_count == 2
        
        # Check shared store was updated
        assert "last_checkpoint" in shared_data
        assert shared_data["last_checkpoint"]["name"] == "test"
        
        # Check return value
        assert result == "continue"
    
    def test_generate_user_output_analysis_flow(self, node):
        """Test user output generation for analysis flow."""
        shared = {
            "requirement_mapping_final": {
                "REQ001": {
                    "requirement": "Python experience",
                    "evidence": ["5 years Python"],
                    "strength": "HIGH",
                    "notes": "Strong match"
                }
            }
        }
        
        config = {
            "flow_name": "analysis",
            "checkpoint_data": ["requirement_mapping_final"]
        }
        
        output = node._generate_user_output(shared, config)
        
        # Check reformatting occurred
        assert "requirement_mappings" in output
        assert "requirement_mapping_final" not in output
        assert output["requirement_mappings"][0]["requirement_id"] == "REQ001"
        assert output["requirement_mappings"][0]["strength"] == "HIGH"
    
    def test_generate_user_output_narrative_flow(self, node):
        """Test user output generation for narrative flow."""
        shared = {
            "narrative_strategy": {
                "must_tell_experiences": ["Led team of 10"],
                "career_arc": {"past": "Engineer", "present": "Lead"},
                "key_messages": ["Technical leadership"],
                "evidence_stories": ["Scaled system 10x"],
                "differentiators": ["Full-stack expertise"]
            }
        }
        
        config = {
            "flow_name": "narrative",
            "checkpoint_data": ["narrative_strategy"]
        }
        
        output = node._generate_user_output(shared, config)
        
        # Check structure is preserved
        assert "narrative_strategy" in output
        strategy = output["narrative_strategy"]
        assert "must_tell_experiences" in strategy
        assert "career_arc" in strategy
        assert "key_messages" in strategy
        assert "evidence_stories" in strategy
        assert "differentiators" in strategy
    
    @patch('yaml.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.symlink_to')
    def test_post_with_custom_user_message(self, mock_symlink, mock_exists, mock_mkdir, mock_file, mock_yaml_dump, node, shared_data):
        """Test post with custom user message."""
        prep_res = {}
        exec_res = {
            "checkpoint_path": Path("checkpoints/test.yaml"),
            "output_path": Path("outputs/test.yaml"),
            "latest_link": Path("checkpoints/latest.yaml"),
            "config": {
                "flow_name": "test",
                "checkpoint_name": "test",
                "timestamp": datetime.now(),
                "checkpoint_data": [],
                "user_message": "Custom instructions:\n- Edit carefully\n- Save when done",
                "node_class": "SaveCheckpointNode",
                "format_version": "1.0"
            }
        }
        
        mock_exists.return_value = False
        
        node.post(shared_data, prep_res, exec_res)
        
        # Check custom message was written
        write_calls = mock_file.return_value.__enter__.return_value.write.call_args_list
        custom_message_written = any("Custom instructions:" in str(call) for call in write_calls)
        assert custom_message_written
    
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_post_handles_file_errors(self, mock_exists, mock_mkdir, mock_open, node, shared_data):
        """Test post handles file writing errors gracefully."""
        prep_res = {}
        exec_res = {
            "checkpoint_path": Path("checkpoints/test.yaml"),
            "output_path": Path("outputs/test.yaml"),
            "latest_link": Path("checkpoints/latest.yaml"),
            "config": {
                "flow_name": "test",
                "checkpoint_name": "test",
                "timestamp": datetime.now(),
                "checkpoint_data": [],
                "user_message": None,
                "node_class": "SaveCheckpointNode",
                "format_version": "1.0"
            }
        }
        
        mock_exists.return_value = False
        mock_open.side_effect = PermissionError("Cannot write file")
        
        with pytest.raises(PermissionError):
            node.post(shared_data, prep_res, exec_res)
    
    def test_checkpoint_data_structure(self, node, shared_data):
        """Test checkpoint data has correct structure."""
        prep_res = {}
        exec_res = {
            "checkpoint_path": Path("test.yaml"),
            "output_path": Path("output.yaml"),
            "latest_link": Path("latest.yaml"),
            "config": {
                "flow_name": "test",
                "checkpoint_name": "test",
                "timestamp": datetime.now(),
                "checkpoint_data": ["requirements", "gaps"],
                "user_message": None,
                "node_class": "SaveCheckpointNode",
                "format_version": "1.0"
            }
        }
        
        # Mock file operations
        written_data = {'checkpoint': None, 'output': None}
        call_count = [0]
        
        def mock_dump(data, file, **kwargs):
            # First call is checkpoint, second is output
            if call_count[0] == 0:
                written_data['checkpoint'] = data
            else:
                written_data['output'] = data
            call_count[0] += 1
        
        with patch('builtins.open', mock_open()):
            with patch('yaml.dump', side_effect=mock_dump):
                with patch('pathlib.Path.mkdir'):
                    with patch('pathlib.Path.exists', return_value=False):
                        with patch('pathlib.Path.symlink_to'):
                            node.post(shared_data, prep_res, exec_res)
        
        # Verify checkpoint structure
        checkpoint = written_data.get('checkpoint', {})
        assert "metadata" in checkpoint
        assert "shared_state" in checkpoint
        assert "recovery_info" in checkpoint
        
        # Verify metadata
        metadata = checkpoint["metadata"]
        assert metadata["checkpoint_name"] == "test"
        assert metadata["flow_name"] == "test"
        assert metadata["node_class"] == "SaveCheckpointNode"
        assert metadata["format_version"] == "1.0"
        
        # Verify recovery info
        recovery = checkpoint["recovery_info"]
        assert recovery["can_resume"] is True
        assert recovery["required_state_keys"] == ["requirements", "gaps"]
    
    def test_set_params_with_custom_action(self, node):
        """Test setting custom action parameter."""
        node.set_params({"action": "pause"})
        
        prep_res = {}
        exec_res = {
            "checkpoint_path": Path("test.yaml"),
            "output_path": Path("output.yaml"),
            "latest_link": Path("latest.yaml"),
            "config": {
                "flow_name": "test",
                "checkpoint_name": "test",
                "timestamp": datetime.now(),
                "checkpoint_data": [],
                "user_message": None,
                "node_class": "SaveCheckpointNode",
                "format_version": "1.0"
            }
        }
        
        with patch('builtins.open', mock_open()):
            with patch('pathlib.Path.mkdir'):
                with patch('pathlib.Path.exists', return_value=False):
                    with patch('pathlib.Path.symlink_to'):
                        result = node.post({}, prep_res, exec_res)
        
        assert result == "pause"