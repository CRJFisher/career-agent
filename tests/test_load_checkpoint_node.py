"""Unit tests for LoadCheckpointNode."""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import yaml
from datetime import datetime, timedelta

from nodes import LoadCheckpointNode


class TestLoadCheckpointNode:
    """Test suite for LoadCheckpointNode."""
    
    @pytest.fixture
    def node(self):
        """Create LoadCheckpointNode instance."""
        return LoadCheckpointNode()
    
    @pytest.fixture
    def valid_checkpoint_data(self):
        """Valid checkpoint data structure."""
        return {
            "metadata": {
                "checkpoint_name": "test_checkpoint",
                "flow_name": "analysis",
                "timestamp": datetime.now().isoformat(),
                "node_class": "SaveCheckpointNode",
                "format_version": "1.0"
            },
            "shared_state": {
                "requirements": {"REQ001": "Python experience"},
                "gaps": ["Cloud experience"],
                "last_checkpoint": {
                    "output_file": "outputs/analysis_output.yaml"
                }
            },
            "recovery_info": {
                "next_action": "continue",
                "can_resume": True,
                "required_state_keys": ["requirements", "gaps"]
            }
        }
    
    @pytest.fixture
    def user_edits_data(self):
        """Sample user edits."""
        return {
            "requirements": {
                "REQ001": "Python experience (5+ years)",
                "REQ002": "AWS experience"
            },
            "new_field": "User added this"
        }
    
    def test_init_default(self, node):
        """Test default initialization."""
        assert node.checkpoint_name is None
        assert node.auto_detect is True
        assert node.checkpoint_dir == Path("checkpoints")
        assert node.output_dir == Path("outputs")
    
    def test_init_with_params(self):
        """Test initialization with parameters."""
        node = LoadCheckpointNode(checkpoint_name="specific_checkpoint", auto_detect=False)
        assert node.checkpoint_name == "specific_checkpoint"
        assert node.auto_detect is False
    
    def test_prep_with_checkpoint_name(self, node):
        """Test prep with specific checkpoint name."""
        node.checkpoint_name = "test_checkpoint"
        
        with patch.object(node, '_find_specific_checkpoint') as mock_find:
            mock_find.return_value = Path("checkpoints/test_checkpoint.yaml")
            
            result = node.prep({})
            
            assert result["checkpoint_path"] == Path("checkpoints/test_checkpoint.yaml")
            assert result["flow_name"] == "workflow"
            assert "load_timestamp" in result
    
    def test_prep_with_auto_detect(self, node):
        """Test prep with auto-detect."""
        shared = {"flow_name": "analysis"}
        
        with patch.object(node, '_find_latest_checkpoint') as mock_find:
            mock_find.return_value = Path("checkpoints/analysis/latest.yaml")
            
            result = node.prep(shared)
            
            assert result["checkpoint_path"] == Path("checkpoints/analysis/latest.yaml")
            assert result["flow_name"] == "analysis"
    
    def test_prep_no_checkpoint_error(self):
        """Test prep fails when no checkpoint specified."""
        node = LoadCheckpointNode(auto_detect=False)
        
        with pytest.raises(ValueError, match="No checkpoint specified"):
            node.prep({})
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_exec_loads_checkpoint(self, mock_yaml_load, mock_file, node, valid_checkpoint_data):
        """Test exec loads checkpoint data."""
        prep_res = {
            "checkpoint_path": Path("checkpoints/test.yaml"),
            "flow_name": "analysis"
        }
        
        mock_yaml_load.return_value = valid_checkpoint_data
        
        with patch.object(node, '_validate_checkpoint'):
            with patch.object(node, '_load_user_edits', return_value={}):
                with patch.object(node, '_merge_checkpoint_and_edits') as mock_merge:
                    mock_merge.return_value = valid_checkpoint_data["shared_state"]
                    with patch.object(node, '_detect_modifications', return_value=[]):
                        
                        result = node.exec(prep_res)
        
        assert result["checkpoint_path"] == str(prep_res["checkpoint_path"])
        assert result["metadata"] == valid_checkpoint_data["metadata"]
        assert result["shared_state"] == valid_checkpoint_data["shared_state"]
        assert result["recovery_info"] == valid_checkpoint_data["recovery_info"]
    
    def test_exec_handles_load_error(self, node):
        """Test exec handles checkpoint load errors."""
        prep_res = {
            "checkpoint_path": Path("nonexistent.yaml"),
            "flow_name": "test"
        }
        
        with pytest.raises(RuntimeError, match="Failed to load checkpoint"):
            node.exec(prep_res)
    
    def test_post_updates_shared_store(self, node):
        """Test post updates shared store correctly."""
        shared = {"existing_data": "value"}
        prep_res = {"checkpoint_path": Path("test.yaml")}
        exec_res = {
            "checkpoint_path": "test.yaml",
            "metadata": {"checkpoint_name": "test", "timestamp": "2024-01-01T12:00:00"},
            "merged_state": {"new_data": "from checkpoint", "requirements": ["REQ001"]},
            "modifications": [],
            "recovery_info": {"next_action": "continue"}
        }
        
        result = node.post(shared, prep_res, exec_res)
        
        # Check shared was updated
        assert shared["new_data"] == "from checkpoint"
        assert shared["requirements"] == ["REQ001"]
        assert shared["existing_data"] == "value"  # Preserved
        
        # Check resumption metadata
        assert "resumed_from_checkpoint" in shared
        resume_info = shared["resumed_from_checkpoint"]
        assert resume_info["checkpoint_name"] == "test"
        assert resume_info["modifications_count"] == 0
        
        # Check return value
        assert result == "continue"
    
    def test_post_with_clear_existing(self, node):
        """Test post with clear_existing parameter."""
        shared = {"existing_data": "will be cleared"}
        node.set_params({"clear_existing": True})
        
        exec_res = {
            "checkpoint_path": "test.yaml",
            "metadata": {},
            "merged_state": {"new_data": "from checkpoint"},
            "modifications": [],
            "recovery_info": {}
        }
        
        node.post(shared, {}, exec_res)
        
        # Check existing data was cleared
        assert "existing_data" not in shared
        assert shared["new_data"] == "from checkpoint"
    
    def test_find_latest_checkpoint_with_symlink(self, node):
        """Test finding latest checkpoint via symlink."""
        flow_checkpoint_dir = node.checkpoint_dir / "analysis"
        
        with patch.object(Path, 'exists') as mock_exists:
            with patch.object(Path, 'glob') as mock_glob:
                # Mock symlink
                mock_link = Mock(spec=Path)
                mock_link.exists.return_value = True
                mock_link.resolve.return_value = Path("checkpoints/analysis/checkpoint_20240101.yaml")
                
                mock_glob.return_value = [mock_link]
                mock_exists.return_value = True
                
                result = node._find_latest_checkpoint("analysis")
                
                assert result == Path("checkpoints/analysis/checkpoint_20240101.yaml")
    
    def test_find_latest_checkpoint_by_mtime(self, node):
        """Test finding latest checkpoint by modification time."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'glob') as mock_glob:
                # Mock checkpoint files
                old_checkpoint = Mock(spec=Path)
                old_checkpoint.is_symlink.return_value = False
                old_checkpoint.name = "checkpoint_old.yaml"
                old_checkpoint.stat.return_value = Mock(st_mtime=1000)
                
                new_checkpoint = Mock(spec=Path)
                new_checkpoint.is_symlink.return_value = False
                new_checkpoint.name = "checkpoint_new.yaml"
                new_checkpoint.stat.return_value = Mock(st_mtime=2000)
                
                mock_glob.return_value = [old_checkpoint, new_checkpoint]
                
                result = node._find_latest_checkpoint("test")
                
                assert result == new_checkpoint
    
    def test_find_latest_checkpoint_not_found(self, node):
        """Test error when no checkpoints found."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'glob', return_value=[]):
                
                with pytest.raises(FileNotFoundError, match="No checkpoints found"):
                    node._find_latest_checkpoint("nonexistent")
    
    def test_find_specific_checkpoint(self, node):
        """Test finding specific checkpoint by name."""
        with patch.object(Path, 'exists') as mock_exists:
            with patch.object(Path, 'glob') as mock_glob:
                # Test exact match
                exact_path = node.checkpoint_dir / "analysis" / "test_checkpoint.yaml"
                mock_exists.side_effect = lambda p=exact_path: p == exact_path
                
                result = node._find_specific_checkpoint("test_checkpoint", "analysis")
                
                assert result == exact_path
    
    def test_validate_checkpoint_valid(self, node, valid_checkpoint_data):
        """Test checkpoint validation with valid data."""
        # Should not raise
        node._validate_checkpoint(valid_checkpoint_data)
    
    def test_validate_checkpoint_missing_fields(self, node):
        """Test validation with missing required fields."""
        invalid_data = {"metadata": {}}  # Missing shared_state
        
        with pytest.raises(ValueError, match="missing 'shared_state'"):
            node._validate_checkpoint(invalid_data)
    
    def test_validate_checkpoint_incompatible_version(self, node, valid_checkpoint_data):
        """Test validation with incompatible version."""
        valid_checkpoint_data["metadata"]["format_version"] = "2.0"
        
        with pytest.raises(ValueError, match="Incompatible checkpoint version"):
            node._validate_checkpoint(valid_checkpoint_data)
    
    def test_validate_checkpoint_old_timestamp(self, node, valid_checkpoint_data):
        """Test validation warns about old checkpoint."""
        old_time = (datetime.now() - timedelta(days=35)).isoformat()
        valid_checkpoint_data["metadata"]["timestamp"] = old_time
        
        with patch('nodes.logger.warning') as mock_warning:
            node._validate_checkpoint(valid_checkpoint_data)
            
            mock_warning.assert_called_with("Checkpoint is 35 days old")
    
    def test_is_version_compatible(self, node):
        """Test version compatibility checking."""
        assert node._is_version_compatible("1.0") is True
        assert node._is_version_compatible("1.5") is True
        assert node._is_version_compatible("2.0") is False
        assert node._is_version_compatible("invalid") is False
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_user_edits(self, mock_yaml_load, mock_file, node, user_edits_data):
        """Test loading user edits from output file."""
        shared_state = {
            "last_checkpoint": {
                "output_file": "outputs/test_output.yaml"
            }
        }
        metadata = {"flow_name": "test"}
        
        # Add comment fields to test filtering
        edits_with_comments = user_edits_data.copy()
        edits_with_comments["# Instructions"] = "Edit this file"
        
        mock_yaml_load.return_value = edits_with_comments
        
        with patch.object(Path, 'exists', return_value=True):
            result = node._load_user_edits(shared_state, metadata)
        
        # Check comments were filtered out
        assert "# Instructions" not in result
        assert result["requirements"] == user_edits_data["requirements"]
        assert result["new_field"] == user_edits_data["new_field"]
    
    def test_load_user_edits_no_file(self, node):
        """Test loading user edits when no file exists."""
        shared_state = {}
        metadata = {"flow_name": "test"}
        
        with patch.object(Path, 'exists', return_value=False):
            result = node._load_user_edits(shared_state, metadata)
        
        assert result == {}
    
    def test_merge_checkpoint_and_edits(self, node):
        """Test merging checkpoint state with user edits."""
        checkpoint_state = {
            "requirements": {"REQ001": "Python"},
            "gaps": ["Cloud"],
            "unchanged": "value"
        }
        
        user_edits = {
            "requirements": {"REQ001": "Python (edited)", "REQ002": "New req"},
            "new_field": "Added by user"
        }
        
        result = node._merge_checkpoint_and_edits(checkpoint_state, user_edits)
        
        # Check merge results
        assert result["requirements"] == user_edits["requirements"]  # Replaced
        assert result["gaps"] == ["Cloud"]  # Preserved
        assert result["unchanged"] == "value"  # Preserved
        assert result["new_field"] == "Added by user"  # Added
    
    def test_detect_modifications_simple(self, node):
        """Test modification detection with simple changes."""
        original = {
            "field1": "original",
            "field2": {"nested": "value"},
            "field3": [1, 2, 3]
        }
        
        modified = {
            "field1": "modified",  # Changed
            "field2": {"nested": "value", "new": "added"},  # Added nested
            "field3": [1, 2, 3, 4],  # List extended
            "field4": "new"  # Added
        }
        
        mods = node._detect_modifications(original, modified)
        
        # Find specific modifications
        field1_mod = next(m for m in mods if m["path"] == "field1")
        assert field1_mod["action"] == "modified"
        assert field1_mod["original"] == "original"
        assert field1_mod["modified"] == "modified"
        
        field2_new_mod = next(m for m in mods if m["path"] == "field2.new")
        assert field2_new_mod["action"] == "added"
        
        field3_mod = next(m for m in mods if m["path"] == "field3")
        assert field3_mod["action"] == "list_size_changed"
        
        field4_mod = next(m for m in mods if m["path"] == "field4")
        assert field4_mod["action"] == "added"
    
    def test_detect_modifications_type_change(self, node):
        """Test modification detection with type changes."""
        original = {"field": "string"}
        modified = {"field": 123}
        
        mods = node._detect_modifications(original, modified)
        
        assert len(mods) == 1
        assert mods[0]["action"] == "type_changed"
        assert mods[0]["original_type"] == "str"
        assert mods[0]["modified_type"] == "int"
    
    def test_detect_modifications_deletion(self, node):
        """Test modification detection with deletions."""
        original = {"field1": "value", "field2": "delete me"}
        modified = {"field1": "value"}
        
        mods = node._detect_modifications(original, modified)
        
        deletion_mod = next(m for m in mods if m["path"] == "field2")
        assert deletion_mod["action"] == "deleted"
        assert deletion_mod["original"] == "delete me"
    
    def test_integration_full_workflow(self, node, valid_checkpoint_data, user_edits_data):
        """Test complete checkpoint loading workflow."""
        shared = {"existing": "data"}
        
        # Mock file operations
        with patch.object(node, '_find_latest_checkpoint') as mock_find:
            mock_find.return_value = Path("checkpoints/test.yaml")
            
            with patch('builtins.open', mock_open(read_data=yaml.dump(valid_checkpoint_data))):
                with patch('yaml.safe_load', side_effect=[valid_checkpoint_data, user_edits_data]):
                    with patch.object(Path, 'exists', return_value=True):
                        
                        # Execute workflow
                        prep_res = node.prep(shared)
                        exec_res = node.exec(prep_res)
                        result = node.post(shared, prep_res, exec_res)
        
        # Verify results
        assert "resumed_from_checkpoint" in shared
        assert shared["requirements"] == user_edits_data["requirements"]  # User edits applied
        assert result == "continue"  # From recovery_info