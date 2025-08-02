"""
Integration tests for the complete job application pipeline.

These tests verify the end-to-end flow works correctly with all components.
They use mock LLM responses to ensure deterministic behavior.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import yaml
from pathlib import Path
import shutil

from main import process_job_application, initialize_shared_store
from utils.llm_wrapper import LLMWrapper


class TestEndToEndPipeline(unittest.TestCase):
    """Test complete pipeline execution with mocked LLM responses."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for outputs
        self.temp_dir = tempfile.mkdtemp()
        self.outputs_dir = Path(self.temp_dir) / "outputs"
        self.outputs_dir.mkdir()
        
        # Sample career database
        self.career_db = {
            "personal_info": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "(555) 123-4567",
                "location": "San Francisco, CA"
            },
            "experience": [{
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "duration": "2020-2023",
                "location": "San Francisco, CA",
                "description": "Led backend development team",
                "achievements": [
                    "Built microservices handling 1M requests/day",
                    "Reduced latency by 40% through optimization",
                    "Mentored 5 junior engineers"
                ],
                "technologies": ["Python", "Django", "PostgreSQL", "AWS", "Docker"]
            }, {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "duration": "2018-2020",
                "location": "San Francisco, CA",
                "description": "Full-stack development",
                "achievements": [
                    "Developed React frontend for SaaS platform",
                    "Implemented REST APIs serving 10K users",
                    "Set up CI/CD pipeline"
                ],
                "technologies": ["JavaScript", "React", "Node.js", "MongoDB"]
            }],
            "education": [{
                "degree": "BS",
                "field": "Computer Science",
                "institution": "UC Berkeley",
                "graduation_year": "2018"
            }],
            "skills": {
                "languages": ["Python", "JavaScript", "Go"],
                "frameworks": ["Django", "React", "Flask"],
                "databases": ["PostgreSQL", "MongoDB", "Redis"],
                "cloud": ["AWS", "GCP"],
                "tools": ["Docker", "Kubernetes", "Git", "Jenkins"]
            }
        }
        
        # Sample job description
        self.job_description = """
        Senior Backend Engineer
        
        We're looking for an experienced backend engineer to join our team.
        
        Requirements:
        - 5+ years backend development experience
        - Strong Python skills with Django or Flask
        - Experience with PostgreSQL and Redis
        - AWS cloud experience
        - Microservices architecture experience
        
        Nice to have:
        - Kubernetes experience
        - Go programming language
        - Team leadership experience
        """
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    @patch('utils.llm_wrapper.LLMWrapper.generate')
    @patch('pathlib.Path.mkdir')
    @patch.object(Path, 'write_text')
    def test_complete_pipeline_execution(self, mock_write, mock_mkdir, mock_llm):
        """Test full pipeline from job description to final documents."""
        # Mock LLM responses for each stage
        mock_responses = {
            # Requirements extraction
            "extract_requirements": {
                "required": [
                    "5+ years backend development experience",
                    "Strong Python skills with Django or Flask",
                    "Experience with PostgreSQL and Redis",
                    "AWS cloud experience",
                    "Microservices architecture experience"
                ],
                "nice_to_have": [
                    "Kubernetes experience",
                    "Go programming language",
                    "Team leadership experience"
                ]
            },
            # Company research (minimal)
            "company_research": {
                "mission": "Building innovative software solutions",
                "culture": "Collaborative and fast-paced",
                "team_scope": "Backend team of 10 engineers"
            },
            # Narrative strategy
            "narrative_strategy": {
                "positioning_statement": "Experienced backend engineer with proven microservices expertise",
                "must_tell_experiences": [{
                    "experience": "TechCorp - Senior Software Engineer",
                    "why_relevant": "Direct microservices experience at scale",
                    "key_points": ["Built services handling 1M requests/day", "Python/Django expertise"]
                }],
                "key_messages": [
                    "Strong Python/Django background matching requirements",
                    "Proven AWS and microservices experience",
                    "Leadership experience mentoring engineers"
                ],
                "differentiators": [
                    "Combined backend expertise with team leadership",
                    "Experience with exact tech stack required"
                ]
            }
        }
        
        # Configure mock to return different responses based on prompt content
        def mock_generate(prompt, *args, **kwargs):
            if "Extract job requirements" in prompt:
                return yaml.dump(mock_responses["extract_requirements"])
            elif "company research" in prompt.lower():
                return yaml.dump(mock_responses["company_research"])
            elif "narrative strategy" in prompt:
                return yaml.dump(mock_responses["narrative_strategy"])
            elif "requirement mapping" in prompt.lower():
                # Return mapping YAML
                return """
- requirement: "5+ years backend development experience"
  evidence:
    - "5 years total: 3 at TechCorp + 2 at StartupXYZ"
  strength: HIGH
- requirement: "Strong Python skills with Django or Flask"
  evidence:
    - "3 years Python/Django at TechCorp"
  strength: HIGH
"""
            elif "gap analysis" in prompt.lower():
                return "gaps: []"  # No gaps
            elif "suitability" in prompt.lower():
                return """
technical_fit_score: 90
cultural_fit_score: 85
key_strengths:
  - Perfect technical match
  - Leadership experience
overall_recommendation: Strong candidate
"""
            elif "prioritize experiences" in prompt.lower():
                return """
- experience: "TechCorp - Senior Software Engineer"
  relevance_score: 95
  key_achievements:
    - Microservices at scale
    - Team leadership
"""
            elif "generate" in prompt.lower() and "cv" in prompt.lower():
                return """
# Test User

## Professional Summary
Experienced backend engineer with 5+ years building scalable systems.

## Professional Experience

### Senior Software Engineer | TechCorp
*San Francisco, CA | 2020-2023*

Led backend development team building microservices.

**Key Achievements:**
- Built microservices handling 1M requests/day
- Reduced latency by 40% through optimization
- Mentored 5 junior engineers

**Technologies:** Python, Django, PostgreSQL, AWS, Docker
"""
            elif "cover letter" in prompt.lower():
                return """
Test User
test@example.com
(555) 123-4567

January 15, 2024

Dear Hiring Manager,

I am writing to express my interest in the Senior Backend Engineer position.

With 5+ years of backend development experience, including 3 years working with Python and Django at TechCorp, I am well-equipped to contribute to your team.

My experience building microservices that handle over 1 million requests per day directly aligns with your needs.

I am excited about the opportunity to bring my skills to your team.

Sincerely,
Test User
"""
            else:
                return "{}"  # Default empty response
        
        mock_llm.side_effect = mock_generate
        
        # Run the pipeline with outputs directory mocked
        with patch('main.Path') as mock_path:
            # Make Path() return our temp directory
            mock_path.return_value = Path(self.outputs_dir)
            mock_path.return_value.mkdir = MagicMock()
            mock_path.return_value.__truediv__ = lambda self, x: Path(self.outputs_dir) / x
            
            result = process_job_application(
                job_description=self.job_description,
                career_db=self.career_db,
                job_title="Senior Backend Engineer",
                company_name="TechStartup",
                skip_company_research=True  # Skip to speed up test
            )
        
        # Verify shared store has expected outputs
        self.assertIsNotNone(result.get("requirements"))
        self.assertIsNotNone(result.get("narrative_strategy"))
        self.assertIsNotNone(result.get("cv_markdown"))
        self.assertIsNotNone(result.get("cover_letter_text"))
        
        # Verify CV content
        self.assertIn("Test User", result["cv_markdown"])
        self.assertIn("Senior Software Engineer | TechCorp", result["cv_markdown"])
        self.assertIn("Python, Django", result["cv_markdown"])
        
        # Verify cover letter content
        self.assertIn("Dear Hiring Manager", result["cover_letter_text"])
        self.assertIn("5+ years of backend development", result["cover_letter_text"])
    
    def test_shared_store_data_flow(self):
        """Test that data flows correctly through shared store."""
        shared = initialize_shared_store(
            career_db=self.career_db,
            job_description=self.job_description,
            job_title="Backend Engineer",
            company_name="TestCo"
        )
        
        # Simulate data being added by each flow
        shared["requirements"] = {
            "required": ["Python", "AWS"],
            "nice_to_have": ["Kubernetes"]
        }
        
        shared["requirement_mapping_final"] = {
            "Python": {"evidence": ["3 years at TechCorp"], "strength": "HIGH"}
        }
        
        shared["gaps"] = []
        shared["coverage_score"] = 90
        
        shared["suitability_assessment"] = {
            "technical_fit_score": 85,
            "cultural_fit_score": 80
        }
        
        shared["narrative_strategy"] = {
            "positioning_statement": "Experienced engineer",
            "must_tell_experiences": []
        }
        
        # Verify all data is accessible
        self.assertEqual(shared["requirements"]["required"], ["Python", "AWS"])
        self.assertEqual(shared["coverage_score"], 90)
        self.assertEqual(shared["suitability_assessment"]["technical_fit_score"], 85)
    
    @patch('utils.llm_wrapper.LLMWrapper.generate')
    def test_checkpoint_pause_and_resume(self, mock_llm):
        """Test that checkpoints work correctly."""
        # This is more of a flow test, but important for integration
        
        # Mock checkpoint save by having AnalysisFlow return "pause"
        with patch('main.AnalysisFlow') as mock_analysis:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "pause"
            mock_analysis.return_value = mock_instance
            
            # Also mock RequirementExtractionFlow to add requirements
            with patch('main.RequirementExtractionFlow') as mock_req:
                req_instance = MagicMock()
                def add_reqs(shared):
                    shared["requirements"] = {"required": ["Python"]}
                req_instance.run.side_effect = add_reqs
                mock_req.return_value = req_instance
                
                result = process_job_application(
                    job_description=self.job_description,
                    career_db=self.career_db,
                    job_title="Engineer",
                    company_name="Corp"
                )
                
                # Should have stopped at checkpoint
                self.assertIsNotNone(result.get("requirements"))
                self.assertIsNone(result.get("cv_markdown"))  # Shouldn't reach generation


class TestErrorHandling(unittest.TestCase):
    """Test error handling in the pipeline."""
    
    def test_missing_requirements_stops_pipeline(self):
        """Test pipeline stops gracefully if requirements extraction fails."""
        with patch('main.RequirementExtractionFlow') as mock_req:
            # Make requirements extraction not add requirements
            mock_instance = MagicMock()
            mock_instance.run.return_value = None
            mock_req.return_value = mock_instance
            
            result = process_job_application(
                job_description="Test",
                career_db={},
                job_title="Test",
                company_name="Test"
            )
            
            # Should stop early
            self.assertIsNone(result.get("requirements"))
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_missing_checkpoint_file(self, mock_open):
        """Test graceful handling of missing checkpoint."""
        from main import resume_workflow
        
        with patch('pathlib.Path.exists', return_value=False):
            result = resume_workflow("analysis")
            
            # Should return empty dict
            self.assertEqual(result, {})


class TestPerformance(unittest.TestCase):
    """Test performance characteristics of the pipeline."""
    
    @patch('utils.llm_wrapper.LLMWrapper.generate')
    def test_pipeline_completes_within_timeout(self, mock_llm):
        """Test that pipeline completes in reasonable time."""
        import time
        
        # Mock instant LLM responses
        mock_llm.return_value = "{}"
        
        start_time = time.time()
        
        # Run with minimal options
        with patch('main.export_final_materials'):
            process_job_application(
                job_description="Test job",
                career_db={"experience": []},
                job_title="Test",
                company_name="Test",
                skip_company_research=True
            )
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly with mocked LLM
        self.assertLess(elapsed_time, 5.0, "Pipeline took too long")


if __name__ == "__main__":
    unittest.main()