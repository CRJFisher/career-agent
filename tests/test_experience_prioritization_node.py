"""
Tests for ExperiencePrioritizationNode.

Tests the pure Python scoring algorithm for prioritizing career experiences
based on weighted criteria.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any, List

from nodes import ExperiencePrioritizationNode


class TestExperiencePrioritizationNode:
    """Test suite for ExperiencePrioritizationNode."""
    
    @pytest.fixture
    def node(self):
        """Create node instance."""
        return ExperiencePrioritizationNode()
    
    @pytest.fixture
    def sample_career_db(self):
        """Create sample career database."""
        return {
            "professional_experience": [
                {
                    "role": "Senior Software Engineer",
                    "company": "TechCorp",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "achievements": [
                        "Led team of 5 engineers to deliver microservices platform",
                        "Reduced API latency by 40% through optimization",
                        "Implemented CI/CD pipeline serving 50+ developers"
                    ],
                    "technologies": ["Python", "AWS", "Docker", "Kubernetes"]
                },
                {
                    "role": "Software Engineer",
                    "company": "StartupXYZ",
                    "start_date": "2019-06",
                    "end_date": "2021-12",
                    "achievements": [
                        "Built REST APIs handling 1M+ requests/day",
                        "Developed React frontend used by 10k users",
                        "Contributed to open source projects"
                    ],
                    "technologies": ["JavaScript", "React", "Node.js", "PostgreSQL"]
                },
                {
                    "role": "Junior Developer",
                    "company": "OldCorp",
                    "start_date": "2017-01",
                    "end_date": "2019-05",
                    "achievements": [
                        "Maintained legacy Java applications",
                        "Fixed bugs and improved performance",
                        "Wrote unit tests"
                    ],
                    "technologies": ["Java", "Spring", "MySQL"]
                }
            ],
            "projects": [
                {
                    "name": "ML Pipeline Automation",
                    "date": "2023-06",
                    "description": "Automated ML model training and deployment",
                    "impact": "Reduced model deployment time from days to hours",
                    "technologies": ["Python", "Kubernetes", "MLflow", "AWS"]
                },
                {
                    "name": "Personal Blog Platform",
                    "date": "2020-03",
                    "description": "Built a blog platform with markdown support",
                    "technologies": ["Python", "Django", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "State University",
                    "graduation_date": "2017-05",
                    "achievements": ["Dean's List", "Capstone Project: AI Chess Engine"]
                }
            ]
        }
    
    @pytest.fixture
    def sample_requirements(self):
        """Create sample job requirements."""
        return {
            "required_skills": ["Python", "AWS", "Kubernetes", "Microservices"],
            "preferred_skills": ["Machine Learning", "Docker", "React"],
            "technologies": ["Python", "Kubernetes", "AWS"],
            "industry": "Cloud Infrastructure"
        }
    
    @pytest.fixture
    def shared_store(self, sample_career_db, sample_requirements):
        """Create shared store with career db and requirements."""
        return {
            "career_db": sample_career_db,
            "requirements": sample_requirements,
            "current_date": "2024-01-01"
        }
    
    def test_node_initialization(self, node):
        """Test node is initialized with correct settings."""
        assert node.max_retries == 1
        assert node.wait == 0  # No wait for deterministic logic
        assert node.WEIGHTS["relevance"] == 0.40
        assert node.WEIGHTS["recency"] == 0.20
        assert node.WEIGHTS["impact"] == 0.20
        assert node.WEIGHTS["uniqueness"] == 0.10
        assert node.WEIGHTS["growth"] == 0.10
        assert sum(node.WEIGHTS.values()) == 1.0  # Weights sum to 1
    
    def test_prep_extracts_all_experiences(self, node, shared_store):
        """Test prep extracts experiences from all sources."""
        context = node.prep(shared_store)
        
        # Should have 3 professional + 2 projects + 1 education = 6 total
        assert len(context["experiences"]) == 6
        
        # Check types are correctly labeled
        type_counts = {}
        for exp in context["experiences"]:
            type_counts[exp["type"]] = type_counts.get(exp["type"], 0) + 1
        
        assert type_counts["professional"] == 3
        assert type_counts["project"] == 2
        assert type_counts["education"] == 1
    
    def test_relevance_scoring(self, node, sample_requirements):
        """Test relevance scoring against requirements."""
        # High relevance experience (matches many requirements)
        high_relevance = {
            "role": "Senior Python Developer",
            "achievements": ["Built microservices on AWS with Kubernetes"],
            "technologies": ["Python", "AWS", "Kubernetes", "Docker"]
        }
        
        # Low relevance experience  
        low_relevance = {
            "role": "PHP Developer",
            "achievements": ["Maintained WordPress sites"],
            "technologies": ["PHP", "MySQL", "WordPress"]
        }
        
        high_score = node._score_relevance(high_relevance, sample_requirements)
        low_score = node._score_relevance(low_relevance, sample_requirements)
        
        assert high_score > 60  # Should score high (66.67% match)
        assert low_score < 20   # Should score low
        assert high_score > low_score
    
    def test_recency_scoring(self, node):
        """Test recency scoring based on dates."""
        current_date = "2024-01-01"
        
        # Current role
        current = {"end_date": "Present"}
        assert node._score_recency(current, current_date) == 100
        
        # Recent role (1 year ago)
        recent = {"end_date": "2023-01-01"}
        assert node._score_recency(recent, current_date) == 90
        
        # Old role (5 years ago)
        old = {"end_date": "2019-01-01"}
        assert node._score_recency(old, current_date) == 50
        
        # Very old role (15 years ago)
        very_old = {"end_date": "2009-01-01"}
        assert node._score_recency(very_old, current_date) == 0
    
    def test_impact_scoring(self, node):
        """Test impact scoring based on quantified achievements."""
        # High impact with numbers
        high_impact = {
            "achievements": [
                "Increased revenue by 40%",
                "Reduced costs by $2M annually",
                "Improved performance by 10x"
            ]
        }
        
        # Low impact without numbers
        low_impact = {
            "achievements": [
                "Worked on various projects",
                "Collaborated with team",
                "Wrote documentation"
            ]
        }
        
        high_score = node._score_impact(high_impact)
        low_score = node._score_impact(low_impact)
        
        assert high_score > 80
        assert low_score < 20
        assert high_score > low_score
    
    def test_uniqueness_scoring(self, node):
        """Test uniqueness scoring compared to other experiences."""
        # Unique ML experience
        unique_exp = {
            "role": "Machine Learning Engineer",
            "description": "Built recommendation systems using deep learning",
            "technologies": ["TensorFlow", "PyTorch", "Kubeflow"]
        }
        
        # Common web dev experience
        common_exp = {
            "role": "Web Developer",
            "description": "Built websites using React",
            "technologies": ["React", "JavaScript", "CSS"]
        }
        
        # Other experiences for comparison
        all_experiences = [
            {"data": unique_exp},
            {"data": common_exp},
            {"data": {"role": "Frontend Developer", "technologies": ["React", "JavaScript"]}},
            {"data": {"role": "Full Stack Developer", "technologies": ["React", "Node.js"]}}
        ]
        
        unique_score = node._score_uniqueness(unique_exp, all_experiences)
        common_score = node._score_uniqueness(common_exp, all_experiences)
        
        assert unique_score > common_score
        assert unique_score > 70  # ML experience should be unique
        # Note: common_score may be high if few comparison experiences
    
    def test_growth_scoring(self, node):
        """Test growth demonstration scoring."""
        # High growth experience
        high_growth = {
            "role": "Engineering Manager",
            "achievements": [
                "Promoted from senior to principal to manager",
                "Grew team from 3 to 15 engineers",
                "Led department transformation"
            ]
        }
        
        # Low growth experience
        low_growth = {
            "role": "Developer",
            "achievements": [
                "Maintained existing systems",
                "Fixed bugs",
                "Updated documentation"
            ]
        }
        
        high_score = node._score_growth(high_growth)
        low_score = node._score_growth(low_growth)
        
        assert high_score > 80
        assert low_score < 30
        assert high_score > low_score
    
    def test_composite_scoring(self, node, shared_store):
        """Test composite score calculation with weights."""
        context = node.prep(shared_store)
        result = node.exec(context)
        
        scored_experiences = result["scored_experiences"]
        
        # Verify all experiences are scored
        assert len(scored_experiences) == len(context["experiences"])
        
        # Verify composite scores are calculated correctly
        for scored_exp in scored_experiences:
            scores = scored_exp["scores"]
            expected_composite = sum(
                scores[criterion] * node.WEIGHTS[criterion]
                for criterion in node.WEIGHTS
            )
            assert abs(scored_exp["composite_score"] - expected_composite) < 0.01
        
        # Verify sorting (highest score first)
        composite_scores = [exp["composite_score"] for exp in scored_experiences]
        assert composite_scores == sorted(composite_scores, reverse=True)
    
    def test_post_creates_prioritized_list(self, node, shared_store):
        """Test post creates properly formatted prioritized list."""
        context = node.prep(shared_store)
        exec_result = node.exec(context)
        
        # Clear any existing prioritized experiences
        shared_store["prioritized_experiences"] = None
        
        action = node.post(shared_store, context, exec_result)
        
        assert action == "prioritize"
        assert "prioritized_experiences" in shared_store
        
        prioritized = shared_store["prioritized_experiences"]
        
        # Check structure
        assert len(prioritized) > 0
        for i, exp in enumerate(prioritized):
            assert exp["rank"] == i + 1
            assert "title" in exp
            assert "type" in exp
            assert "composite_score" in exp
            assert "scores" in exp
            assert "data" in exp
            
            # Verify all score components present
            assert set(exp["scores"].keys()) == set(node.WEIGHTS.keys())
    
    def test_deterministic_results(self, node, shared_store):
        """Test that scoring is deterministic (same input = same output)."""
        # Run scoring multiple times
        results = []
        for _ in range(3):
            context = node.prep(shared_store)
            result = node.exec(context)
            
            # Extract composite scores
            scores = [exp["composite_score"] for exp in result["scored_experiences"]]
            results.append(scores)
        
        # All runs should produce identical results
        for i in range(1, len(results)):
            assert results[i] == results[0]
    
    def test_edge_case_empty_career_db(self, node):
        """Test handling of empty career database."""
        shared = {
            "career_db": {},
            "requirements": {"required_skills": ["Python"]},
            "current_date": "2024-01-01"
        }
        
        context = node.prep(shared)
        assert context["experiences"] == []
        
        result = node.exec(context)
        assert result["scored_experiences"] == []
        
        action = node.post(shared, context, result)
        assert action == "prioritize"
        assert shared["prioritized_experiences"] == []
    
    def test_edge_case_missing_dates(self, node):
        """Test handling of experiences with missing dates."""
        experience = {
            "role": "Developer",
            "company": "SomeCompany"
            # No dates provided
        }
        
        score = node._score_recency(experience, "2024-01-01")
        assert score == 100  # No date defaults to current_date, which gets max score
    
    def test_edge_case_no_requirements(self, node):
        """Test relevance scoring when no requirements provided."""
        experience = {
            "role": "Software Engineer",
            "technologies": ["Python", "JavaScript"]
        }
        
        score = node._score_relevance(experience, {})
        assert score == 50  # Should get default score
    
    def test_text_extraction(self, node):
        """Test text extraction from complex experience structure."""
        experience = {
            "role": "Senior Engineer",
            "company": "TechCorp",
            "description": "Led engineering team",
            "achievements": [
                "Achievement 1",
                "Achievement 2"
            ],
            "projects": [
                {"name": "Project A", "description": "Built system"},
                {"name": "Project B", "impact": "Saved $1M"}
            ],
            "nested": {
                "should_not_extract": "This is too nested"
            }
        }
        
        text = node._get_experience_text(experience)
        
        assert "Senior Engineer" in text
        assert "TechCorp" in text
        assert "Led engineering team" in text
        assert "Achievement 1" in text
        assert "Achievement 2" in text
        assert "Project A" in text
        assert "Built system" in text
        assert "Saved $1M" in text
    
    def test_scoring_weights_sum_to_one(self, node):
        """Test that scoring weights sum to 1.0."""
        total_weight = sum(node.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001
    
    @pytest.mark.parametrize("num_experiences", [10, 50, 100])
    def test_performance_with_large_db(self, node, num_experiences):
        """Test performance with large career databases."""
        import time
        
        # Generate large career db
        large_db = {
            "professional_experience": [
                {
                    "role": f"Role {i}",
                    "company": f"Company {i}",
                    "start_date": f"{2020-i}-01",
                    "end_date": "Present" if i == 0 else f"{2021-i}-12",
                    "achievements": [f"Achievement {j}" for j in range(3)],
                    "technologies": ["Python", "AWS", "Docker"]
                }
                for i in range(num_experiences)
            ]
        }
        
        shared = {
            "career_db": large_db,
            "requirements": {"required_skills": ["Python", "AWS"]},
            "current_date": "2024-01-01"
        }
        
        start_time = time.time()
        context = node.prep(shared)
        result = node.exec(context)
        node.post(shared, context, result)
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0  # Less than 1 second
        
        # Should produce valid results
        assert len(shared["prioritized_experiences"]) == num_experiences