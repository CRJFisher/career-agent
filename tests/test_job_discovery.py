"""Tests for job discovery agent functionality."""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from nodes_job_discovery import (
    InitializeSearchNode,
    CrawlJobBoardNode,
    ExtractJobListingsNode,
    FilterRelevantJobsNode,
    DeduplicateJobsNode,
    SaveJobsNode
)
from flow_job_discovery import JobDiscoveryAgent, create_default_root_urls


class TestInitializeSearchNode:
    """Test InitializeSearchNode."""
    
    def test_prep(self):
        """Test prep method."""
        node = InitializeSearchNode()
        shared = {
            "career_database": {"test": "data"},
            "search_preferences": {"location": "SF"},
            "root_urls": ["http://test.com"],
            "max_crawl_depth": 5
        }
        
        result = node.prep(shared)
        
        assert result["career_database"] == {"test": "data"}
        assert result["search_preferences"]["location"] == "SF"
        assert result["root_urls"] == ["http://test.com"]
        assert result["max_depth"] == 5
    
    def test_exec_with_skills_and_experiences(self):
        """Test exec with career database containing skills and experiences."""
        node = InitializeSearchNode()
        prep_res = {
            "career_database": {
                "skills": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"]
                },
                "experiences": [
                    {"title": "Senior Software Engineer", "period": "2020-2023"},
                    {"title": "Software Engineer", "period": "2018-2020"}
                ]
            },
            "search_preferences": {
                "location": "San Francisco",
                "remote": True
            },
            "root_urls": ["https://linkedin.com/jobs"],
            "max_depth": 3,
            "max_pages": 100
        }
        
        result = node.exec(prep_res)
        
        assert "Python" in result["search_params"]["keywords"]
        assert "Senior Software Engineer" in result["search_params"]["job_titles"]
        assert result["search_params"]["location"] == "San Francisco"
        assert result["search_params"]["remote_ok"] == True
        assert result["search_params"]["experience_level"] in ["mid", "senior"]
        assert result["crawl_config"]["max_depth"] == 3
    
    def test_linkedin_url_enhancement(self):
        """Test that LinkedIn URLs are enhanced with search parameters."""
        node = InitializeSearchNode()
        prep_res = {
            "career_database": {
                "skills": {"languages": ["Python", "Go", "Java"]}
            },
            "search_preferences": {"location": "New York"},
            "root_urls": ["https://linkedin.com/jobs"],
            "max_depth": 3,
            "max_pages": 100
        }
        
        result = node.exec(prep_res)
        
        # Should enhance LinkedIn URL with keywords
        enhanced_url = result["root_urls"][0]
        assert "keywords=" in enhanced_url
        assert "location=New York" in enhanced_url
    
    def test_experience_level_determination(self):
        """Test experience level calculation."""
        node = InitializeSearchNode()
        
        # Test entry level
        career_db = {"experiences": [{"period": "2023-2024"}]}
        level = node._determine_experience_level(career_db)
        assert level == "entry"
        
        # Test senior level
        career_db = {"experiences": [
            {"period": "2018-2024"},
            {"period": "2015-2018"}
        ]}
        level = node._determine_experience_level(career_db)
        assert level == "senior"


class TestCrawlJobBoardNode:
    """Test CrawlJobBoardNode."""
    
    @pytest.mark.asyncio
    async def test_job_url_detection(self):
        """Test job URL pattern detection."""
        node = CrawlJobBoardNode()
        
        # LinkedIn job URLs
        assert node._is_job_listing_url(
            "https://linkedin.com/jobs/view/123456", "linkedin.com"
        )
        assert not node._is_job_listing_url(
            "https://linkedin.com/jobs/search/", "linkedin.com"
        )
        
        # Indeed job URLs
        assert node._is_job_listing_url(
            "https://indeed.com/viewjob?jk=abc123", "indeed.com"
        )
        
        # Generic patterns
        assert node._is_job_listing_url(
            "https://company.com/job/12345", "company.com"
        )
        assert node._is_job_listing_url(
            "https://careers.com/position/98765", "careers.com"
        )
    
    def test_job_board_identification(self):
        """Test job board identification from URL."""
        node = CrawlJobBoardNode()
        
        assert node._identify_job_board("https://linkedin.com/jobs/view/123") == "linkedin"
        assert node._identify_job_board("https://indeed.com/viewjob?jk=123") == "indeed"
        assert node._identify_job_board("https://glassdoor.com/job-listing/") == "glassdoor"
        assert node._identify_job_board("https://wellfound.com/jobs/123") == "wellfound"
        assert node._identify_job_board("https://random.com/jobs") == "other"
    
    @pytest.mark.asyncio
    async def test_crawl_with_mock_scraper(self):
        """Test crawling with mocked scraper."""
        node = CrawlJobBoardNode()
        
        # Mock the scraper
        with patch('nodes_job_discovery.AISimpleScraper') as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.extract_content = AsyncMock(return_value={
                "success": True,
                "links": [
                    "/jobs/view/123",
                    "/jobs/view/456",
                    "/jobs/search?page=2"
                ]
            })
            
            prep_res = {
                "root_urls": ["https://linkedin.com/jobs/search/"],
                "crawl_config": {
                    "max_pages": 10,
                    "max_depth": 2,
                    "delay_between_requests": 0.1
                },
                "discovered_urls": set()
            }
            
            result = await node.exec_async(prep_res)
            
            assert result["pages_crawled"] > 0
            assert result["total_discovered"] >= 2
            assert len(result["discovered_jobs"]) >= 2


class TestExtractJobListingsNode:
    """Test ExtractJobListingsNode."""
    
    @pytest.mark.asyncio
    async def test_job_extraction(self):
        """Test job extraction from URLs."""
        node = ExtractJobListingsNode()
        
        # Mock dependencies
        with patch('nodes_job_discovery.LLMWrapper') as MockLLM, \
             patch('nodes_job_discovery.AISimpleScraper') as MockScraper:
            
            # Mock scraper
            mock_scraper = MockScraper.return_value
            mock_scraper.extract_content = AsyncMock(return_value={
                "success": True,
                "text": "Senior Software Engineer at TechCorp...",
                "metadata": {"title": "Senior Software Engineer - TechCorp"}
            })
            
            # Mock LLM
            mock_llm = MockLLM.return_value
            mock_llm.call_llm = AsyncMock(return_value=json.dumps({
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "salary_range": "$150k-$200k",
                "required_skills": ["Python", "AWS", "Docker"],
                "nice_to_have_skills": ["Kubernetes", "React"],
                "years_experience": "5+",
                "job_type": "Full-time"
            }))
            
            prep_res = {
                "discovered_jobs": [
                    {
                        "url": "https://example.com/job/123",
                        "board": "linkedin",
                        "discovered_at": datetime.now().isoformat()
                    }
                ],
                "extraction_batch_size": 1,
                "search_params": {}
            }
            
            result = await node.exec_async(prep_res)
            
            assert len(result["extracted_jobs"]) == 1
            assert result["extraction_success_rate"] == 1.0
            
            job = result["extracted_jobs"][0]
            assert job["success"] == True
            assert job["job_data"]["title"] == "Senior Software Engineer"
            assert job["job_data"]["company"] == "TechCorp"


class TestFilterRelevantJobsNode:
    """Test FilterRelevantJobsNode."""
    
    @pytest.mark.asyncio
    async def test_job_relevance_scoring(self):
        """Test job relevance scoring."""
        node = FilterRelevantJobsNode()
        
        with patch('nodes_job_discovery.LLMWrapper') as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.call_llm = AsyncMock(return_value=json.dumps({
                "overall_score": 0.85,
                "skills_match": 0.9,
                "experience_match": 0.8,
                "location_match": 1.0,
                "career_progression": 0.7,
                "culture_fit": 0.6,
                "key_strengths": ["Strong Python skills", "AWS experience"],
                "concerns": ["No React experience"],
                "recommendation": "strong_match"
            }))
            
            prep_res = {
                "extracted_jobs": [{
                    "job_data": {
                        "title": "Senior Python Developer",
                        "company": "TechCorp",
                        "required_skills": ["Python", "AWS"]
                    },
                    "source_url": "https://example.com/job/123"
                }],
                "career_database": {
                    "experiences": [{
                        "title": "Python Developer",
                        "company": "StartupXYZ",
                        "period": "2020-2023"
                    }],
                    "skills": {
                        "languages": ["Python", "JavaScript"],
                        "cloud": ["AWS", "GCP"]
                    }
                },
                "search_params": {"location": "San Francisco"},
                "min_relevance_score": 0.6
            }
            
            result = await node.exec_async(prep_res)
            
            assert len(result["relevant_jobs"]) == 1
            assert result["relevant_jobs"][0]["relevance_score"]["overall_score"] == 0.85
            assert result["avg_relevance_score"] == 0.85


class TestDeduplicateJobsNode:
    """Test DeduplicateJobsNode."""
    
    def test_job_deduplication(self):
        """Test job deduplication logic."""
        node = DeduplicateJobsNode()
        
        prep_res = {
            "relevant_jobs": [
                {
                    "job_data": {
                        "title": "Software Engineer",
                        "company": "TechCorp",
                        "location": "SF"
                    },
                    "source_url": "https://linkedin.com/jobs/view/123",
                    "job_board": "linkedin"
                },
                {
                    "job_data": {
                        "title": "Software Engineer",
                        "company": "TechCorp",
                        "location": "SF"
                    },
                    "source_url": "https://indeed.com/viewjob?jk=456",
                    "job_board": "indeed"
                },
                {
                    "job_data": {
                        "title": "Senior Engineer",
                        "company": "DifferentCorp",
                        "location": "NYC"
                    },
                    "source_url": "https://linkedin.com/jobs/view/789",
                    "job_board": "linkedin"
                }
            ],
            "existing_jobs": []
        }
        
        result = node.exec(prep_res)
        
        # Should deduplicate the two TechCorp jobs
        assert len(result["unique_jobs"]) == 2
        assert result["duplicates_removed"] == 1


class TestSaveJobsNode:
    """Test SaveJobsNode."""
    
    def test_save_jobs_json(self, tmp_path):
        """Test saving jobs in JSON format."""
        node = SaveJobsNode()
        
        output_path = tmp_path / "test_jobs.json"
        
        prep_res = {
            "unique_jobs": [
                {
                    "job_data": {
                        "title": "Software Engineer",
                        "company": "TechCorp"
                    },
                    "relevance_score": {
                        "overall_score": 0.85,
                        "recommendation": "strong_match"
                    },
                    "source_url": "https://example.com/job/123",
                    "job_board": "linkedin"
                }
            ],
            "output_format": "json",
            "output_path": str(output_path),
            "discovery_stats": {
                "total_discovered": 10,
                "total_extracted": 5,
                "total_relevant": 1
            }
        }
        
        result = node.exec(prep_res)
        
        assert result["jobs_saved"] == 1
        assert output_path.exists()
        
        # Verify saved content
        with open(output_path) as f:
            saved_data = json.load(f)
        
        assert saved_data["total_jobs"] == 1
        assert len(saved_data["jobs"]) == 1
        assert saved_data["jobs"][0]["job_data"]["title"] == "Software Engineer"
    
    def test_summary_report_generation(self):
        """Test summary report generation."""
        node = SaveJobsNode()
        
        jobs = [
            {
                "job_data": {
                    "title": "Senior Engineer",
                    "company": "TechCorp",
                    "location": "San Francisco"
                },
                "relevance_score": {
                    "overall_score": 0.9,
                    "recommendation": "strong_match",
                    "key_strengths": ["Python expertise", "Cloud experience"]
                },
                "source_url": "https://example.com/job/123"
            }
        ]
        
        stats = {
            "total_discovered": 100,
            "total_extracted": 50,
            "total_relevant": 10,
            "avg_relevance_score": 0.75
        }
        
        report = node._generate_summary_report(jobs, stats)
        
        assert "Job Discovery Summary" in report
        assert "Total URLs Discovered: 100" in report
        assert "Senior Engineer at TechCorp" in report
        assert "90.00%" in report  # relevance score


class TestJobDiscoveryAgent:
    """Test JobDiscoveryAgent flow."""
    
    def test_flow_initialization(self):
        """Test flow initialization."""
        config = {
            "max_pages_per_site": 50,
            "min_relevance_score": 0.7
        }
        
        agent = JobDiscoveryAgent(config)
        assert agent.config["max_pages_per_site"] == 50
        assert agent.config["min_relevance_score"] == 0.7
    
    def test_prepare_shared_state(self):
        """Test shared state preparation."""
        agent = JobDiscoveryAgent()
        
        career_db = {"skills": {"languages": ["Python"]}}
        root_urls = ["https://linkedin.com/jobs"]
        search_prefs = {"location": "SF"}
        
        shared = agent.prepare_shared_state(
            career_database=career_db,
            root_urls=root_urls,
            search_preferences=search_prefs
        )
        
        assert shared["career_database"] == career_db
        assert shared["root_urls"] == root_urls
        assert shared["search_preferences"]["location"] == "SF"
        assert shared["max_pages_per_site"] == 100  # default
        assert shared["min_relevance_score"] == 0.6  # default


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_default_root_urls(self):
        """Test default root URL generation."""
        urls = create_default_root_urls(
            job_titles=["Python Developer", "Software Engineer"],
            location="San Francisco",
            remote_ok=True
        )
        
        assert len(urls) >= 3  # At least LinkedIn, Indeed, Glassdoor
        
        # Check LinkedIn URL
        linkedin_url = next(u for u in urls if "linkedin.com" in u)
        assert "keywords=Python+Developer" in linkedin_url
        assert "location=San+Francisco" in linkedin_url
        assert "f_WT=2" in linkedin_url  # remote filter
        
        # Check Indeed URL
        indeed_url = next(u for u in urls if "indeed.com" in u)
        assert "q=Python+Developer" in indeed_url
        assert "l=San+Francisco" in indeed_url