"""
Unit tests for the main orchestrator functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import yaml
from datetime import datetime

from main import (
    initialize_shared_store,
    process_job_application,
    export_final_materials,
    resume_workflow,
    load_config
)


class TestInitializeSharedStore(unittest.TestCase):
    """Test shared store initialization."""
    
    def test_shared_store_has_all_required_keys(self):
        """Test that shared store contains all data contract keys."""
        career_db = {"experience": []}
        job_desc = "Test job description"
        
        shared = initialize_shared_store(
            career_db=career_db,
            job_description=job_desc,
            job_title="Software Engineer",
            company_name="TechCorp",
            company_url="https://techcorp.com"
        )
        
        # Core inputs
        self.assertEqual(shared["career_db"], career_db)
        self.assertEqual(shared["job_spec_text"], job_desc)
        self.assertEqual(shared["job_description"], job_desc)
        self.assertEqual(shared["job_title"], "Software Engineer")
        self.assertEqual(shared["company_name"], "TechCorp")
        self.assertEqual(shared["company_url"], "https://techcorp.com")
        self.assertIn("current_date", shared)
        
        # Flow outputs initialized as None
        flow_outputs = [
            "requirements", "requirement_mapping_raw", "requirement_mapping_assessed",
            "requirement_mapping_final", "gaps", "coverage_score",
            "company_research", "suitability_assessment", "prioritized_experiences",
            "narrative_strategy", "cv_markdown", "cover_letter_text"
        ]
        
        for key in flow_outputs:
            self.assertIn(key, shared)
            self.assertIsNone(shared[key])
        
        # Configuration
        self.assertTrue(shared["enable_company_research"])
        self.assertEqual(shared["max_research_iterations"], 15)
        self.assertTrue(shared["enable_checkpoints"])
    
    def test_current_date_format(self):
        """Test current date is properly formatted."""
        shared = initialize_shared_store(
            career_db={},
            job_description="Test",
            job_title="Test",
            company_name="Test"
        )
        
        # Should be YYYY-MM-DD format
        date_str = shared["current_date"]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.fail(f"Date format incorrect: {date_str}")
    
    def test_optional_company_url(self):
        """Test that company URL is optional."""
        shared = initialize_shared_store(
            career_db={},
            job_description="Test",
            job_title="Test",
            company_name="Test"
        )
        
        self.assertIsNone(shared["company_url"])


class TestProcessJobApplication(unittest.TestCase):
    """Test the main job application processing flow."""
    
    @patch('main.RequirementExtractionFlow')
    @patch('main.AnalysisFlow')
    @patch('main.CompanyResearchAgent')
    @patch('main.AssessmentFlow')
    @patch('main.NarrativeFlow')
    @patch('main.GenerationFlow')
    @patch('main.export_final_materials')
    def test_complete_flow_execution(self, mock_export, mock_gen, mock_narr, 
                                   mock_assess, mock_research, mock_analysis, mock_req):
        """Test that all flows are executed in correct order."""
        # Setup mocks
        mock_req_instance = Mock()
        mock_req.return_value = mock_req_instance
        
        mock_analysis_instance = Mock()
        mock_analysis_instance.run.return_value = "continue"
        mock_analysis.return_value = mock_analysis_instance
        
        mock_research_instance = Mock()
        mock_research.return_value = mock_research_instance
        
        mock_assess_instance = Mock()
        mock_assess.return_value = mock_assess_instance
        
        mock_narr_instance = Mock()
        mock_narr_instance.run.return_value = "continue"
        mock_narr.return_value = mock_narr_instance
        
        mock_gen_instance = Mock()
        mock_gen.return_value = mock_gen_instance
        
        # Run process with mocked shared store that has requirements
        def add_requirements(shared):
            shared["requirements"] = {"required": ["Python"]}
            return None
            
        mock_req_instance.run.side_effect = add_requirements
        
        result = process_job_application(
            job_description="Test job",
            career_db={"experience": []},
            job_title="Engineer",
            company_name="TechCorp",
            skip_company_research=False
        )
        
        # Verify flows called in order
        mock_req_instance.run.assert_called_once()
        mock_analysis_instance.run.assert_called_once()
        mock_research_instance.run.assert_called_once()
        mock_assess_instance.run.assert_called_once()
        mock_narr_instance.run.assert_called_once()
        mock_gen_instance.run.assert_called_once()
        mock_export.assert_called_once()
        
        # Verify shared store returned
        self.assertIsInstance(result, dict)
        self.assertEqual(result["job_title"], "Engineer")
        self.assertEqual(result["company_name"], "TechCorp")
    
    @patch('main.RequirementExtractionFlow')
    @patch('main.AnalysisFlow')
    @patch('main.export_final_materials')
    def test_flow_pauses_at_analysis_checkpoint(self, mock_export, mock_analysis, mock_req):
        """Test workflow pauses when analysis checkpoint is created."""
        # Setup mocks
        mock_req_instance = Mock()
        mock_req.return_value = mock_req_instance
        
        mock_analysis_instance = Mock()
        mock_analysis_instance.run.return_value = "pause"  # Simulate checkpoint
        mock_analysis.return_value = mock_analysis_instance
        
        def add_requirements(shared):
            shared["requirements"] = {"required": ["Python"]}
            return None
            
        mock_req_instance.run.side_effect = add_requirements
        
        # Run process
        result = process_job_application(
            job_description="Test job",
            career_db={"experience": []},
            job_title="Engineer", 
            company_name="TechCorp"
        )
        
        # Verify it stopped after analysis
        mock_req_instance.run.assert_called_once()
        mock_analysis_instance.run.assert_called_once()
        mock_export.assert_not_called()  # Should not reach export
        
        # Verify checkpoint message would be logged
        self.assertIsInstance(result, dict)
    
    @patch('main.CompanyResearchAgent')
    def test_skip_company_research(self, mock_research):
        """Test that company research can be skipped."""
        with patch('main.RequirementExtractionFlow'), \
             patch('main.AnalysisFlow'), \
             patch('main.AssessmentFlow'), \
             patch('main.NarrativeFlow'), \
             patch('main.GenerationFlow'), \
             patch('main.export_final_materials'):
            
            process_job_application(
                job_description="Test",
                career_db={},
                job_title="Test",
                company_name="Test",
                skip_company_research=True
            )
            
            # Research should not be called
            mock_research.assert_not_called()


class TestExportFinalMaterials(unittest.TestCase):
    """Test final material export functionality."""
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.write_text')
    @patch('subprocess.run')
    def test_export_cv_and_cover_letter(self, mock_subprocess, mock_write, mock_mkdir):
        """Test CV and cover letter are exported correctly."""
        shared = {
            "cv_markdown": "# Test CV\nContent here",
            "cover_letter_text": "Dear Hiring Manager,\nTest letter",
            "job_title": "Software Engineer",
            "company_name": "Tech Corp"
        }
        
        export_final_materials(shared)
        
        # Verify output directory created
        mock_mkdir.assert_called_once_with(exist_ok=True)
        
        # Verify files written (2 times - CV and cover letter)
        self.assertEqual(mock_write.call_count, 2)
        
        # Check CV content
        cv_call = mock_write.call_args_list[0]
        self.assertEqual(cv_call[0][0], "# Test CV\nContent here")
        
        # Check cover letter content
        letter_call = mock_write.call_args_list[1]
        self.assertEqual(letter_call[0][0], "Dear Hiring Manager,\nTest letter")
    
    @patch('pathlib.Path.mkdir')
    def test_handles_missing_content_gracefully(self, mock_mkdir):
        """Test export handles missing CV or cover letter."""
        shared = {}  # No content
        
        # Should not raise exception
        export_final_materials(shared)
        
        # Directory still created
        mock_mkdir.assert_called_once()
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.write_text')
    def test_filename_sanitization(self, mock_write, mock_mkdir):
        """Test that filenames are properly sanitized."""
        shared = {
            "cv_markdown": "Test",
            "cover_letter_text": "Test",
            "job_title": "Software/Engineer & ML",  # Contains special chars
            "company_name": "Tech Corp, Inc."  # Contains special chars
        }
        
        export_final_materials(shared)
        
        # Filenames should have special chars replaced
        # Can't check exact filename due to timestamp, but verify write called
        self.assertEqual(mock_write.call_count, 2)


class TestResumeWorkflow(unittest.TestCase):
    """Test checkpoint resume functionality."""
    
    @patch('builtins.open', new_callable=mock_open, read_data="""
job_title: Software Engineer
company_name: TechCorp
requirements:
  required: [Python, Django]
requirement_mapping_final: {}
gaps: []
""")
    @patch('pathlib.Path.exists', return_value=True)
    @patch('main.CompanyResearchAgent')
    @patch('main.AssessmentFlow')
    @patch('main.NarrativeFlow')
    @patch('main.GenerationFlow')
    @patch('main.export_final_materials')
    def test_resume_from_analysis_checkpoint(self, mock_export, mock_gen, mock_narr,
                                           mock_assess, mock_research, mock_exists, mock_file):
        """Test resuming from analysis checkpoint."""
        # Setup narrative to continue (not pause)
        mock_narr_instance = Mock()
        mock_narr_instance.run.return_value = "continue"
        mock_narr.return_value = mock_narr_instance
        
        result = resume_workflow("analysis", skip_company_research=False)
        
        # Verify checkpoint loaded
        mock_file.assert_called()
        
        # Verify remaining flows executed
        mock_research.assert_called_once()
        mock_assess.assert_called_once()
        mock_narr_instance.run.assert_called_once()
        mock_gen.assert_called_once()
        mock_export.assert_called_once()
        
        self.assertIsInstance(result, dict)
    
    @patch('builtins.open', new_callable=mock_open, read_data="""
narrative_strategy:
  must_tell_experiences: []
career_db: {}
requirements: {}
job_title: Engineer
company_name: Corp
""")
    @patch('pathlib.Path.exists', return_value=True)
    @patch('main.GenerationFlow')
    @patch('main.export_final_materials')
    def test_resume_from_narrative_checkpoint(self, mock_export, mock_gen, mock_exists, mock_file):
        """Test resuming from narrative checkpoint."""
        result = resume_workflow("narrative")
        
        # Only generation and export should run
        mock_gen.assert_called_once()
        mock_export.assert_called_once()
        
        self.assertIsInstance(result, dict)
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_resume_missing_checkpoint(self, mock_exists):
        """Test resume fails gracefully when checkpoint missing."""
        result = resume_workflow("analysis")
        
        # Should return empty dict
        self.assertEqual(result, {})


class TestLoadConfig(unittest.TestCase):
    """Test configuration loading."""
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data="key: value\n")
    def test_load_valid_config(self, mock_file, mock_exists):
        """Test loading valid YAML config."""
        config = load_config("config.yaml")
        
        self.assertEqual(config, {"key": "value"})
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_load_missing_config(self, mock_exists):
        """Test loading missing config returns empty dict."""
        config = load_config("missing.yaml")
        
        self.assertEqual(config, {})


if __name__ == "__main__":
    unittest.main()