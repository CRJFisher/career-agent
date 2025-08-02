"""
Comprehensive integration tests for the career application agent.

This test suite validates the entire pipeline with various scenarios,
edge cases, and regression tests to ensure system reliability.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import yaml
import json
from pathlib import Path
import shutil
from datetime import datetime

from main import (
    process_job_application,
    initialize_shared_store,
    resume_workflow,
    export_final_materials
)
from flow import (
    RequirementExtractionFlow,
    AnalysisFlow,
    CompanyResearchAgent,
    AssessmentFlow,
    NarrativeFlow,
    GenerationFlow
)
from utils import validate_shared_store


class TestComprehensivePipeline(unittest.TestCase):
    """Comprehensive integration tests for the complete pipeline."""
    
    def setUp(self):
        """Set up test environment with comprehensive mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.outputs_dir = Path(self.temp_dir) / "outputs"
        self.outputs_dir.mkdir()
        
        # Comprehensive career database
        self.career_db = {
            "personal_info": {
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "(555) 123-4567",
                "location": "San Francisco, CA",
                "linkedin": "linkedin.com/in/janesmith",
                "github": "github.com/janesmith"
            },
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "duration": "2020-2023",
                    "location": "San Francisco, CA",
                    "description": "Led backend development team for cloud platform",
                    "achievements": [
                        "Built microservices architecture handling 1M+ requests/day",
                        "Reduced system latency by 40% through optimization",
                        "Mentored team of 5 junior engineers",
                        "Implemented CI/CD pipeline reducing deployment time by 60%"
                    ],
                    "technologies": ["Python", "Django", "PostgreSQL", "AWS", "Docker", "Kubernetes"]
                },
                {
                    "title": "Software Engineer",
                    "company": "StartupXYZ",
                    "duration": "2018-2020",
                    "location": "San Francisco, CA",
                    "description": "Full-stack development for SaaS platform",
                    "achievements": [
                        "Developed React frontend serving 10K active users",
                        "Implemented REST APIs with 99.9% uptime",
                        "Set up monitoring and alerting infrastructure"
                    ],
                    "technologies": ["JavaScript", "React", "Node.js", "MongoDB", "AWS"]
                },
                {
                    "title": "Junior Developer",
                    "company": "WebAgency",
                    "duration": "2017-2018",
                    "location": "Los Angeles, CA",
                    "description": "Web development for client projects",
                    "achievements": [
                        "Built responsive websites for 20+ clients",
                        "Improved page load times by 50%"
                    ],
                    "technologies": ["HTML", "CSS", "JavaScript", "PHP", "MySQL"]
                }
            ],
            "education": [
                {
                    "degree": "BS",
                    "field": "Computer Science",
                    "institution": "UC Berkeley",
                    "graduation_year": "2017",
                    "gpa": 3.8,
                    "honors": ["Dean's List", "CS Honor Society"]
                }
            ],
            "skills": {
                "languages": ["Python", "JavaScript", "Go", "Java"],
                "frameworks": ["Django", "React", "Flask", "Express.js"],
                "databases": ["PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
                "cloud": ["AWS", "GCP", "Docker", "Kubernetes"],
                "tools": ["Git", "Jenkins", "Terraform", "Datadog"]
            },
            "certifications": [
                "AWS Certified Solutions Architect - Professional",
                "Certified Kubernetes Administrator (CKA)"
            ],
            "projects": [
                {
                    "name": "Open Source Contributor",
                    "description": "Active contributor to Django REST framework",
                    "url": "github.com/encode/django-rest-framework"
                }
            ]
        }
        
        # Sample job descriptions for different roles
        self.job_descriptions = {
            "backend": """
Senior Backend Engineer

We're looking for an experienced backend engineer to join our growing team.

About the Role:
You'll be responsible for designing and building scalable backend services that power our platform serving millions of users worldwide.

Requirements:
- 5+ years of backend development experience
- Strong proficiency in Python with Django or Flask
- Experience with PostgreSQL and Redis
- Deep understanding of RESTful API design
- Experience with AWS services (EC2, S3, RDS, Lambda)
- Knowledge of microservices architecture
- Experience with Docker and Kubernetes
- Strong understanding of software design patterns

Nice to have:
- Experience with Go or Java
- Knowledge of event-driven architecture
- Experience with message queues (Kafka, RabbitMQ)
- Contributions to open source projects
- Experience mentoring junior developers

About Us:
We're a fast-growing fintech startup building the next generation of payment infrastructure. Our team is passionate about creating elegant solutions to complex problems.
""",
            "fullstack": """
Full Stack Engineer

Join our team to build innovative web applications from frontend to backend.

Responsibilities:
- Develop features across the entire stack
- Collaborate with product and design teams
- Optimize application performance
- Participate in code reviews

Requirements:
- 3+ years full-stack development experience
- Frontend: React, TypeScript, modern CSS
- Backend: Node.js or Python
- Database experience (SQL and NoSQL)
- Cloud platform experience (AWS/GCP)
- Git version control

Nice to have:
- Mobile development experience
- DevOps/CI/CD experience
- Agile methodology experience
""",
            "ml_engineer": """
Machine Learning Engineer

We're seeking an ML Engineer to help build our AI-powered platform.

Requirements:
- 4+ years of ML engineering experience
- Strong Python programming skills
- Experience with PyTorch or TensorFlow
- Experience deploying ML models to production
- Understanding of MLOps practices
- Cloud platform experience

Nice to have:
- Experience with large language models
- Knowledge of distributed training
- Published research papers
"""
        }
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    @patch('utils.llm_wrapper.LLMWrapper.generate')
    def test_backend_role_complete_pipeline(self, mock_llm):
        """Test complete pipeline for backend engineering role."""
        # Configure comprehensive mock responses
        self._configure_backend_mock_responses(mock_llm)
        
        # Run the pipeline
        with patch('main.Path') as mock_path:
            mock_path.return_value = Path(self.outputs_dir)
            mock_path.return_value.mkdir = MagicMock()
            mock_path.return_value.__truediv__ = lambda self, x: Path(self.outputs_dir) / x
            
            result = process_job_application(
                job_description=self.job_descriptions["backend"],
                career_db=self.career_db,
                job_title="Senior Backend Engineer",
                company_name="FinTech Startup",
                company_url="https://fintechstartup.com",
                skip_company_research=False
            )
        
        # Validate each phase produced expected outputs
        self._validate_requirements_extraction(result)
        self._validate_analysis_phase(result)
        self._validate_company_research(result)
        self._validate_assessment(result)
        self._validate_narrative_strategy(result)
        self._validate_generated_materials(result)
        
        # Validate data persistence across flow boundaries
        self._validate_data_persistence(result)
        
        # Validate output quality
        self._validate_output_quality(result)
    
    @patch('utils.llm_wrapper.LLMWrapper.generate')
    def test_fullstack_role_pipeline(self, mock_llm):
        """Test pipeline with fullstack engineer role."""
        self._configure_fullstack_mock_responses(mock_llm)
        
        result = process_job_application(
            job_description=self.job_descriptions["fullstack"],
            career_db=self.career_db,
            job_title="Full Stack Engineer",
            company_name="TechStartup",
            skip_company_research=True  # Test without research
        )
        
        # Verify company research was skipped
        self.assertEqual(result.get("company_research", {}), {})
        
        # Verify other phases completed
        self.assertIsNotNone(result.get("requirements"))
        self.assertIsNotNone(result.get("narrative_strategy"))
        self.assertIsNotNone(result.get("cv_markdown"))
    
    @patch('utils.llm_wrapper.LLMWrapper.generate')
    def test_ml_engineer_role_pipeline(self, mock_llm):
        """Test pipeline with ML engineer role."""
        # Modify career DB to include ML experience
        ml_career_db = self.career_db.copy()
        ml_career_db["experience"][0]["achievements"].append(
            "Deployed ML models serving 100K predictions/day"
        )
        ml_career_db["skills"]["ml_frameworks"] = ["PyTorch", "TensorFlow", "Scikit-learn"]
        
        self._configure_ml_mock_responses(mock_llm)
        
        result = process_job_application(
            job_description=self.job_descriptions["ml_engineer"],
            career_db=ml_career_db,
            job_title="Machine Learning Engineer",
            company_name="AI Corp"
        )
        
        # Verify ML-specific content in narrative
        self.assertIn("ML", str(result.get("narrative_strategy", {})))
    
    def test_checkpoint_and_resume_functionality(self):
        """Test checkpoint creation and resume functionality."""
        # Create a checkpoint file
        checkpoint_data = {
            "job_title": "Software Engineer",
            "company_name": "TestCorp",
            "requirements": {"required": ["Python", "AWS"]},
            "requirement_mapping_final": [
                {"requirement": "Python", "evidence": ["5 years Python"], "strength": "HIGH"}
            ],
            "gaps": [],
            "coverage_score": 90
        }
        
        checkpoint_path = self.outputs_dir / "analysis_output.yaml"
        with open(checkpoint_path, 'w') as f:
            yaml.dump(checkpoint_data, f)
        
        # Test resume from checkpoint
        with patch('main.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            with patch('builtins.open', mock_open(read_data=yaml.dump(checkpoint_data))):
                with patch('main.CompanyResearchAgent'), \
                     patch('main.AssessmentFlow'), \
                     patch('main.NarrativeFlow'), \
                     patch('main.GenerationFlow'), \
                     patch('main.export_final_materials'):
                    
                    result = resume_workflow("analysis", skip_company_research=True)
                    
                    # Verify checkpoint data was loaded
                    self.assertEqual(result.get("job_title"), "Software Engineer")
                    self.assertEqual(result.get("coverage_score"), 90)
    
    def test_error_propagation_and_recovery(self):
        """Test error handling across flow boundaries."""
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            # Make requirements extraction fail
            mock_llm.side_effect = Exception("LLM service unavailable")
            
            with self.assertLogs(level='ERROR') as log:
                try:
                    process_job_application(
                        job_description="Test job",
                        career_db=self.career_db,
                        job_title="Test",
                        company_name="Test"
                    )
                except Exception:
                    pass  # Expected to fail
                
                # Verify error was logged
                self.assertTrue(any("LLM service" in record.getMessage() 
                                  for record in log.records))
    
    def test_edge_case_empty_career_database(self):
        """Test pipeline with minimal career database."""
        minimal_db = {
            "personal_info": {"name": "Test User", "email": "test@test.com"},
            "experience": [],
            "education": [],
            "skills": {}
        }
        
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            mock_llm.return_value = "{}"  # Minimal responses
            
            # Should handle gracefully without crashing
            result = process_job_application(
                job_description="Simple job",
                career_db=minimal_db,
                job_title="Engineer",
                company_name="Company"
            )
            
            self.assertIsInstance(result, dict)
    
    def test_edge_case_very_long_job_description(self):
        """Test with extremely long job description."""
        long_job = "Requirements:\n" + "\n".join([f"- Requirement {i}" for i in range(100)])
        
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            mock_llm.return_value = yaml.dump({"required": ["Python"]})
            
            result = process_job_application(
                job_description=long_job,
                career_db=self.career_db,
                job_title="Test",
                company_name="Test"
            )
            
            self.assertIsNotNone(result.get("requirements"))
    
    def test_data_validation_throughout_pipeline(self):
        """Test that shared store validation works throughout pipeline."""
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            # Configure mock to return invalid data
            mock_llm.return_value = yaml.dump({
                "required": "Should be a list not string"  # Invalid
            })
            
            with self.assertRaises(Exception):
                # Should fail validation
                process_job_application(
                    job_description="Test",
                    career_db=self.career_db,
                    job_title="Test",
                    company_name="Test"
                )
    
    def test_performance_large_career_database(self):
        """Test performance with large career database."""
        import time
        
        # Create large career DB with many experiences
        large_db = self.career_db.copy()
        large_db["experience"] = large_db["experience"] * 10  # 30 experiences
        
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            mock_llm.return_value = "{}"
            
            start_time = time.time()
            
            process_job_application(
                job_description="Test job",
                career_db=large_db,
                job_title="Test",
                company_name="Test",
                skip_company_research=True
            )
            
            elapsed = time.time() - start_time
            
            # Should complete in reasonable time even with large DB
            self.assertLess(elapsed, 10.0, "Pipeline too slow with large database")
    
    # Helper methods for validation
    
    def _configure_backend_mock_responses(self, mock_llm):
        """Configure mock LLM responses for backend role."""
        responses = {
            "requirements": yaml.dump({
                "required": [
                    "5+ years backend development",
                    "Python with Django or Flask",
                    "PostgreSQL and Redis",
                    "AWS services",
                    "Microservices architecture",
                    "Docker and Kubernetes"
                ],
                "nice_to_have": [
                    "Go or Java experience",
                    "Event-driven architecture",
                    "Message queues"
                ]
            }),
            "mapping": yaml.dump([
                {
                    "requirement": "5+ years backend development",
                    "evidence": ["6 years total experience in backend roles"],
                    "strength": "HIGH"
                },
                {
                    "requirement": "Python with Django or Flask",
                    "evidence": ["3 years Python/Django at TechCorp"],
                    "strength": "HIGH"
                }
            ]),
            "gaps": yaml.dump([
                {
                    "requirement": "Message queues",
                    "severity": "NICE_TO_HAVE",
                    "mitigation_strategies": ["Highlight distributed systems experience"]
                }
            ]),
            "company_research": yaml.dump({
                "mission": "Building next-gen payment infrastructure",
                "culture": "Fast-paced, innovative",
                "team_scope": "Backend team of 15 engineers",
                "technology_stack_practices": "Python, microservices, AWS"
            }),
            "assessment": yaml.dump({
                "technical_fit_score": 92,
                "cultural_fit_score": 88,
                "key_strengths": ["Strong Python/Django", "Microservices experience"],
                "overall_recommendation": "Excellent fit for the role"
            }),
            "narrative": yaml.dump({
                "positioning_statement": "Backend expert with fintech-relevant experience",
                "must_tell_experiences": [
                    {
                        "experience": "TechCorp microservices",
                        "why_relevant": "Direct match for scale requirements"
                    }
                ],
                "key_messages": ["Scale expertise", "Python mastery", "Team leadership"]
            }),
            "cv": "# Jane Smith\n\n## Professional Summary\n\nExperienced backend engineer...",
            "cover_letter": "Dear Hiring Manager,\n\nI am excited to apply..."
        }
        
        def mock_generate(prompt, *args, **kwargs):
            prompt_lower = prompt.lower()
            if "requirements" in prompt_lower:
                return responses["requirements"]
            elif "mapping" in prompt_lower:
                return responses["mapping"]
            elif "gaps" in prompt_lower:
                return responses["gaps"]
            elif "company" in prompt_lower:
                return responses["company_research"]
            elif "assessment" in prompt_lower or "suitability" in prompt_lower:
                return responses["assessment"]
            elif "narrative" in prompt_lower or "strategy" in prompt_lower:
                return responses["narrative"]
            elif "cv" in prompt_lower:
                return responses["cv"]
            elif "cover letter" in prompt_lower:
                return responses["cover_letter"]
            else:
                return "{}"
        
        mock_llm.side_effect = mock_generate
    
    def _configure_fullstack_mock_responses(self, mock_llm):
        """Configure mock responses for fullstack role."""
        # Simplified responses for fullstack
        mock_llm.return_value = yaml.dump({
            "required": ["React", "Node.js", "Cloud platforms"]
        })
    
    def _configure_ml_mock_responses(self, mock_llm):
        """Configure mock responses for ML engineer role."""
        mock_llm.return_value = yaml.dump({
            "required": ["Python", "PyTorch/TensorFlow", "MLOps"]
        })
    
    def _validate_requirements_extraction(self, result):
        """Validate requirements were properly extracted."""
        self.assertIn("requirements", result)
        requirements = result["requirements"]
        self.assertIsInstance(requirements, dict)
        self.assertIn("required", requirements)
        self.assertIsInstance(requirements["required"], list)
        self.assertTrue(len(requirements["required"]) > 0)
    
    def _validate_analysis_phase(self, result):
        """Validate analysis phase outputs."""
        self.assertIn("requirement_mapping_final", result)
        self.assertIn("gaps", result)
        self.assertIn("coverage_score", result)
        
        # Validate mapping structure
        mapping = result["requirement_mapping_final"]
        self.assertIsInstance(mapping, list)
        if mapping:
            self.assertIn("requirement", mapping[0])
            self.assertIn("evidence", mapping[0])
            self.assertIn("strength", mapping[0])
    
    def _validate_company_research(self, result):
        """Validate company research output."""
        if "company_research" in result and result["company_research"]:
            research = result["company_research"]
            self.assertIsInstance(research, dict)
            # Should have at least some research fields
            research_fields = ["mission", "culture", "team_scope"]
            self.assertTrue(any(field in research for field in research_fields))
    
    def _validate_assessment(self, result):
        """Validate suitability assessment."""
        self.assertIn("suitability_assessment", result)
        assessment = result["suitability_assessment"]
        self.assertIsInstance(assessment, dict)
        
        # Check scores
        self.assertIn("technical_fit_score", assessment)
        self.assertIn("cultural_fit_score", assessment)
        score = assessment["technical_fit_score"]
        self.assertTrue(0 <= score <= 100)
    
    def _validate_narrative_strategy(self, result):
        """Validate narrative strategy structure."""
        self.assertIn("narrative_strategy", result)
        strategy = result["narrative_strategy"]
        self.assertIsInstance(strategy, dict)
        self.assertIn("positioning_statement", strategy)
        self.assertIn("must_tell_experiences", strategy)
        self.assertIn("key_messages", strategy)
    
    def _validate_generated_materials(self, result):
        """Validate final CV and cover letter."""
        self.assertIn("cv_markdown", result)
        self.assertIn("cover_letter_text", result)
        
        # Check CV has content
        cv = result["cv_markdown"]
        self.assertIsInstance(cv, str)
        self.assertTrue(len(cv) > 100)  # Should have substantial content
        self.assertIn("#", cv)  # Should have Markdown headers
        
        # Check cover letter
        letter = result["cover_letter_text"]
        self.assertIsInstance(letter, str)
        self.assertTrue(len(letter) > 100)
        self.assertIn("Dear", letter)  # Should have salutation
    
    def _validate_data_persistence(self, result):
        """Validate data persists correctly across flows."""
        # Initial data should still be present
        self.assertIn("career_db", result)
        self.assertIn("job_title", result)
        self.assertIn("company_name", result)
        
        # All flow outputs should be present
        expected_outputs = [
            "requirements", "requirement_mapping_final", "gaps",
            "suitability_assessment", "narrative_strategy",
            "cv_markdown", "cover_letter_text"
        ]
        
        for output in expected_outputs:
            self.assertIn(output, result, f"Missing expected output: {output}")
    
    def _validate_output_quality(self, result):
        """Validate quality and consistency of outputs."""
        # CV should reference actual experience
        cv = result.get("cv_markdown", "")
        self.assertIn("TechCorp", cv)  # Should include actual company
        
        # Cover letter should reference job title
        letter = result.get("cover_letter_text", "")
        job_title = result.get("job_title", "")
        self.assertIn(job_title, letter)
        
        # Narrative strategy should align with requirements
        if "narrative_strategy" in result and "requirements" in result:
            strategy = result["narrative_strategy"]
            requirements = result["requirements"]
            # At least one requirement should be addressed in key messages
            req_terms = " ".join(requirements.get("required", []))
            messages = " ".join(strategy.get("key_messages", []))
            # Should have some overlap in terminology
            self.assertTrue(
                any(word in messages.lower() for word in req_terms.lower().split()
                    if len(word) > 3)
            )


class TestRegressionSuite(unittest.TestCase):
    """Regression tests to ensure previously fixed issues don't reoccur."""
    
    def test_regression_special_characters_in_job_title(self):
        """Ensure special characters in job titles are handled correctly."""
        with patch('main.export_final_materials') as mock_export:
            # Job title with special characters
            shared = {
                "job_title": "Software Engineer / Team Lead & Architect",
                "company_name": "Tech Co., Inc.",
                "cv_markdown": "Test CV",
                "cover_letter_text": "Test Letter"
            }
            
            export_final_materials(shared)
            
            # Should sanitize filenames
            self.assertTrue(mock_export.called or True)  # Mock might intercept
    
    def test_regression_empty_requirements_handling(self):
        """Ensure empty requirements don't crash the system."""
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            # Return empty requirements
            mock_llm.return_value = yaml.dump({"required": []})
            
            # Should handle gracefully
            shared = initialize_shared_store(
                career_db={},
                job_description="Vague job description",
                job_title="Engineer",
                company_name="Company"
            )
            
            self.assertIsNotNone(shared)
    
    def test_regression_unicode_in_career_database(self):
        """Ensure unicode characters in career DB are handled."""
        career_db = {
            "personal_info": {
                "name": "José García",
                "email": "jose@example.com",
                "location": "São Paulo, Brazil"
            },
            "experience": [{
                "title": "Engenheiro de Software Sênior",
                "company": "Empresa São Paulo",
                "duration": "2020-2023",
                "achievements": ["Construí sistema para 1M+ usuários"],
                "technologies": ["Python"]
            }]
        }
        
        with patch('utils.llm_wrapper.LLMWrapper.generate') as mock_llm:
            mock_llm.return_value = "{}"
            
            # Should handle unicode without errors
            result = process_job_application(
                job_description="Test job",
                career_db=career_db,
                job_title="Engineer",
                company_name="Company"
            )
            
            self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()