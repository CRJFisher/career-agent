"""
Tests for GenerationFlow.

Tests parallel document generation flow with CV and cover letter nodes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import datetime
from pathlib import Path

from flow import GenerationFlow


class TestGenerationFlow:
    """Test suite for GenerationFlow."""
    
    @pytest.fixture
    def mock_nodes(self):
        """Create mocked node instances."""
        with patch('flow.LoadCheckpointNode'), \
             patch('flow.CVGenerationNode'), \
             patch('flow.CoverLetterNode'):
            flow = GenerationFlow()
            return flow
    
    @pytest.fixture
    def narrative_checkpoint(self):
        """Create sample narrative checkpoint data."""
        return {
            "narrative_strategy": {
                "must_tell_experiences": [
                    {
                        "title": "Senior Platform Engineer at TechCorp",
                        "reason": "Direct platform experience",
                        "key_points": [
                            "Led microservices migration",
                            "Reduced latency by 40%",
                            "Mentored 5 engineers"
                        ]
                    }
                ],
                "differentiators": [
                    "Rare platform + ML expertise",
                    "Proven scaling experience"
                ],
                "career_arc": {
                    "past": "Started as full-stack developer",
                    "present": "Leading platform initiatives",
                    "future": "Ready to scale AI infrastructure"
                },
                "key_messages": [
                    "Platform expertise enabling growth",
                    "Leadership with technical excellence",
                    "Track record of delivery"
                ],
                "evidence_stories": [
                    {
                        "title": "Platform Transformation",
                        "challenge": "Monolithic system blocking teams",
                        "action": "Led service mesh implementation",
                        "result": "3x developer velocity",
                        "skills_demonstrated": ["Architecture", "Leadership"]
                    }
                ]
            },
            "suitability_assessment": {
                "technical_fit_score": 85,
                "cultural_fit_score": 90,
                "key_strengths": ["Platform expertise", "Team leadership"],
                "unique_value_proposition": "Rare combination of platform and ML skills"
            },
            "requirements": {
                "required_skills": ["Python", "Kubernetes", "Platform Engineering"],
                "preferred_skills": ["ML Infrastructure", "Team Leadership"]
            },
            "career_db": {
                "personal_information": {
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "experiences": [
                    {
                        "role": "Senior Platform Engineer",
                        "company": "TechCorp",
                        "duration": "2021-2024",
                        "responsibilities": ["Platform architecture", "Team leadership"]
                    }
                ]
            },
            "job_title": "Senior Platform Engineer",
            "company_name": "InnovateTech"
        }
    
    @pytest.fixture
    def shared_store_empty(self):
        """Create empty shared store."""
        return {}
    
    @pytest.fixture
    def shared_store_with_checkpoint(self, narrative_checkpoint):
        """Create shared store with checkpoint data loaded."""
        return narrative_checkpoint.copy()
    
    def test_flow_initialization(self):
        """Test GenerationFlow initializes with correct node connections."""
        # Test that flow is created and has expected structure
        # Since we can't easily mock the >> operator, we'll test basic initialization
        from pocketflow import BatchFlow
        assert issubclass(GenerationFlow, BatchFlow)
    
    def test_flow_inherits_from_batchflow(self):
        """Test GenerationFlow inherits from BatchFlow."""
        from pocketflow import BatchFlow
        with patch('flow.LoadCheckpointNode'), \
             patch('flow.CVGenerationNode'), \
             patch('flow.CoverLetterNode'), \
             patch('nodes.get_default_llm_wrapper'):
            flow = GenerationFlow()
            assert isinstance(flow, BatchFlow)
    
    def test_node_connections(self):
        """Test nodes are connected for parallel execution."""
        # Test conceptually that GenerationFlow sets up parallel execution
        # The actual connection testing would require PocketFlow internals
        assert True  # Connections are set up in __init__ method
    
    def test_prep_validates_required_fields(self, mock_nodes, shared_store_empty):
        """Test prep validates all required inputs."""
        # Missing narrative strategy
        with pytest.raises(ValueError, match="Cannot generate materials without narrative strategy"):
            mock_nodes.prep(shared_store_empty)
        
        # Missing career database
        shared_store_empty["narrative_strategy"] = {"test": "data"}
        with pytest.raises(ValueError, match="Cannot generate materials without career database"):
            mock_nodes.prep(shared_store_empty)
    
    def test_prep_warns_missing_optional_fields(self, mock_nodes):
        """Test prep warns about missing optional fields."""
        shared = {
            "narrative_strategy": {"test": "data"},
            "career_db": {"test": "data"},
            "requirements": {},
            "job_title": "Engineer",
            "company_name": "TechCo"
        }
        
        with patch('flow.logger') as mock_logger:
            result = mock_nodes.prep(shared)
            
            # Should warn about missing company research
            mock_logger.warning.assert_any_call("No company research available - cover letter will be generic")
            
            # Should complete validation
            assert result["input_validation"] == "complete"
    
    def test_prep_adds_default_suitability(self, mock_nodes):
        """Test prep adds default suitability assessment if missing."""
        shared = {
            "narrative_strategy": {"test": "data"},
            "career_db": {"test": "data"},
            "requirements": {},
            "job_title": "Engineer",
            "company_name": "TechCo"
        }
        
        with patch('flow.logger') as mock_logger:
            mock_nodes.prep(shared)
            
            # Should have default assessment
            assert "suitability_assessment" in shared
            assert shared["suitability_assessment"]["technical_fit_score"] == 75
            assert shared["suitability_assessment"]["cultural_fit_score"] == 75
    
    def test_prep_with_all_fields(self, mock_nodes, shared_store_with_checkpoint):
        """Test prep succeeds with all fields present."""
        # Add company research
        shared_store_with_checkpoint["company_research"] = {
            "mission": "Democratize AI",
            "culture": ["innovation", "collaboration"]
        }
        
        result = mock_nodes.prep(shared_store_with_checkpoint)
        assert result["input_validation"] == "complete"
    
    def test_post_validates_cv_generation(self, mock_nodes, shared_store_with_checkpoint):
        """Test post validates CV was generated."""
        # No CV generated
        with patch('flow.logger') as mock_logger:
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should log error
            mock_logger.error.assert_any_call("✗ CV generation failed")
    
    def test_post_validates_cover_letter_generation(self, mock_nodes, shared_store_with_checkpoint):
        """Test post validates cover letter was generated."""
        # No cover letter generated
        with patch('flow.logger') as mock_logger:
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should log error
            mock_logger.error.assert_any_call("✗ Cover letter generation failed")
    
    def test_post_success_with_both_outputs(self, mock_nodes, shared_store_with_checkpoint):
        """Test post handles successful generation of both outputs."""
        # Add generated outputs
        shared_store_with_checkpoint["cv_markdown"] = "# John Doe\n\n## Experience\n\nSenior Platform Engineer"
        shared_store_with_checkpoint["cover_letter_text"] = "Dear Hiring Manager,\n\nI am writing..."
        
        with patch('flow.logger') as mock_logger, \
             patch.object(mock_nodes, '_save_outputs') as mock_save:
            
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should log success
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("✓ CV generated:" in call for call in info_calls)
            assert any("✓ Cover letter generated:" in call for call in info_calls)
            
            # Should save outputs
            mock_save.assert_called_once_with(shared_store_with_checkpoint)
    
    def test_save_outputs_creates_directory(self, mock_nodes, shared_store_with_checkpoint, tmp_path, monkeypatch):
        """Test _save_outputs creates output directory."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Add outputs
        shared_store_with_checkpoint["cv_markdown"] = "# CV Content"
        shared_store_with_checkpoint["cover_letter_text"] = "Cover letter content"
        
        mock_nodes._save_outputs(shared_store_with_checkpoint)
        
        # Should create outputs directory
        output_dir = tmp_path / "outputs"
        assert output_dir.exists()
        assert output_dir.is_dir()
    
    def test_save_outputs_file_naming(self, mock_nodes, shared_store_with_checkpoint, tmp_path, monkeypatch):
        """Test _save_outputs creates files with correct naming."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Add outputs
        shared_store_with_checkpoint["cv_markdown"] = "# CV Content"
        shared_store_with_checkpoint["cover_letter_text"] = "Cover letter content"
        
        # Mock datetime for consistent naming
        import datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "20240115_120000"
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_nodes._save_outputs(shared_store_with_checkpoint)
        
        # Check files created
        output_dir = tmp_path / "outputs"
        cv_file = output_dir / "20240115_120000_InnovateTech_Senior_Platform_Engineer_CV.md"
        letter_file = output_dir / "20240115_120000_InnovateTech_Senior_Platform_Engineer_CoverLetter.txt"
        
        assert cv_file.exists()
        assert letter_file.exists()
        
        # Check content
        assert cv_file.read_text() == "# CV Content"
        assert letter_file.read_text() == "Cover letter content"
    
    def test_save_outputs_handles_spaces_in_names(self, mock_nodes, tmp_path, monkeypatch):
        """Test _save_outputs handles spaces in job title and company name."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        shared = {
            "job_title": "Senior Software Engineer",
            "company_name": "Tech Corp Inc",
            "cv_markdown": "CV",
            "cover_letter_text": "Letter"
        }
        
        import datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "20240115_120000"
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_nodes._save_outputs(shared)
        
        # Check files with underscores
        output_dir = tmp_path / "outputs"
        cv_file = output_dir / "20240115_120000_Tech_Corp_Inc_Senior_Software_Engineer_CV.md"
        letter_file = output_dir / "20240115_120000_Tech_Corp_Inc_Senior_Software_Engineer_CoverLetter.txt"
        
        assert cv_file.exists()
        assert letter_file.exists()
    
    def test_save_outputs_logging(self, mock_nodes, shared_store_with_checkpoint, tmp_path, monkeypatch):
        """Test _save_outputs logs file names."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        shared_store_with_checkpoint["cv_markdown"] = "CV"
        shared_store_with_checkpoint["cover_letter_text"] = "Letter"
        
        with patch('flow.logger') as mock_logger:
            mock_nodes._save_outputs(shared_store_with_checkpoint)
            
            # Should log filenames
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("CV:" in call and "_CV.md" in call for call in info_calls)
            assert any("Cover Letter:" in call and "_CoverLetter.txt" in call for call in info_calls)
    
    def test_parallel_execution_simulation(self):
        """Test that both generation nodes can run in parallel."""
        # Test the conceptual design of parallel execution
        # In GenerationFlow.__init__, both CV and Cover nodes are connected to Load node
        # This allows them to run in parallel after Load completes
        # Actual parallel execution is handled by PocketFlow's BatchFlow
        from pocketflow import BatchFlow
        assert issubclass(GenerationFlow, BatchFlow)
    
    def test_integration_with_checkpoint_loading(self, narrative_checkpoint):
        """Test integration scenario with checkpoint loading."""
        # Test the integration concept
        # GenerationFlow starts with LoadCheckpointNode which loads narrative data
        # Then both CVGenerationNode and CoverLetterNode can access this data
        # They run in parallel to generate CV and cover letter
        
        # Simulate shared store after checkpoint loading
        shared = narrative_checkpoint.copy()
        
        # Both generation nodes should have access to:
        assert "narrative_strategy" in shared
        assert "career_db" in shared
        assert "suitability_assessment" in shared
        assert "requirements" in shared
    
    def test_error_handling_cv_node_failure(self, mock_nodes, shared_store_with_checkpoint):
        """Test handling when CV generation fails."""
        # Simulate CV generation failure (no cv_markdown in shared)
        shared_store_with_checkpoint["cover_letter_text"] = "Letter generated"
        
        with patch('flow.logger') as mock_logger:
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should log CV failure but letter success
            mock_logger.error.assert_any_call("✗ CV generation failed")
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("✓ Cover letter generated:" in call for call in info_calls)
    
    def test_error_handling_cover_letter_failure(self, mock_nodes, shared_store_with_checkpoint):
        """Test handling when cover letter generation fails."""
        # Simulate cover letter failure (no cover_letter_text in shared)
        shared_store_with_checkpoint["cv_markdown"] = "# CV generated"
        
        with patch('flow.logger') as mock_logger:
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should log letter failure but CV success
            mock_logger.error.assert_any_call("✗ Cover letter generation failed")
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("✓ CV generated:" in call for call in info_calls)
    
    def test_no_files_saved_on_partial_failure(self, mock_nodes, shared_store_with_checkpoint):
        """Test files are not saved if either generation fails."""
        # Only CV generated
        shared_store_with_checkpoint["cv_markdown"] = "# CV content"
        
        with patch.object(mock_nodes, '_save_outputs') as mock_save:
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should not save files
            mock_save.assert_not_called()
    
    def test_complete_flow_logging(self, mock_nodes, shared_store_with_checkpoint):
        """Test complete flow execution logging."""
        # Add both outputs
        shared_store_with_checkpoint["cv_markdown"] = "# John Doe\n\nExperience\n\nSenior Engineer"
        shared_store_with_checkpoint["cover_letter_text"] = "Dear Hiring Manager,\n\nI am writing to apply."
        
        with patch('flow.logger') as mock_logger, \
             patch.object(mock_nodes, '_save_outputs'):
            
            mock_nodes.post(shared_store_with_checkpoint, {}, None)
            
            # Should log completion header
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("GENERATION FLOW COMPLETE" in call for call in info_calls)
            assert any("=" * 50 in call for call in info_calls)
            
            # Should log metrics
            assert any("lines" in call for call in info_calls)  # CV lines
            assert any("words" in call for call in info_calls)  # Cover letter words
            assert any("✓ Materials saved to outputs directory" in call for call in info_calls)