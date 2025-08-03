"""Job Discovery Agent Flow

This module implements the autonomous job discovery agent that crawls job boards
to find relevant opportunities based on the user's career profile.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from pocketflow import Flow
from nodes_job_discovery import (
    InitializeSearchNode,
    CrawlJobBoardNode,
    ExtractJobListingsNode,
    FilterRelevantJobsNode,
    DeduplicateJobsNode,
    SaveJobsNode
)

logger = logging.getLogger(__name__)


class JobDiscoveryAgent(Flow):
    """Autonomous agent for discovering job opportunities across multiple job boards.
    
    This flow orchestrates the complete job discovery process:
    1. Initialize search parameters from career profile
    2. Crawl job boards to discover listings
    3. Extract detailed information from job pages
    4. Filter jobs based on relevance
    5. Remove duplicates
    6. Save results with analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the job discovery agent.
        
        Args:
            config: Configuration dictionary with options like:
                - max_pages_per_site: Maximum pages to crawl per job board
                - max_crawl_depth: Maximum depth for crawling
                - min_relevance_score: Minimum score to consider a job relevant
                - extraction_batch_size: Number of jobs to extract in parallel
        """
        self.config = config or {}
        
        # Create nodes
        init_node = InitializeSearchNode()
        crawl_node = CrawlJobBoardNode()
        extract_node = ExtractJobListingsNode()
        filter_node = FilterRelevantJobsNode()
        dedupe_node = DeduplicateJobsNode()
        save_node = SaveJobsNode()
        
        # Build flow
        flow = (
            init_node 
            >> crawl_node 
            >> extract_node 
            >> filter_node 
            >> dedupe_node 
            >> save_node
        )
        
        super().__init__(start=init_node)
        
    def prepare_shared_state(
        self,
        career_database: Dict[str, Any],
        root_urls: List[str],
        search_preferences: Optional[Dict[str, Any]] = None,
        output_path: str = "outputs/discovered_jobs.json"
    ) -> Dict[str, Any]:
        """Prepare the shared state for job discovery.
        
        Args:
            career_database: The user's career database
            root_urls: List of job board URLs to start crawling from
            search_preferences: Optional search preferences like location, salary, etc.
            output_path: Where to save discovered jobs
            
        Returns:
            Initialized shared state dictionary
        """
        shared = {
            "career_database": career_database,
            "root_urls": root_urls,
            "search_preferences": search_preferences or {},
            "output_path": output_path,
            "output_format": "json" if output_path.endswith(".json") else "csv",
            
            # Apply configuration
            "max_pages_per_site": self.config.get("max_pages_per_site", 100),
            "max_crawl_depth": self.config.get("max_crawl_depth", 3),
            "min_relevance_score": self.config.get("min_relevance_score", 0.6),
            "extraction_batch_size": self.config.get("extraction_batch_size", 10),
            
            # Optional: Previously discovered jobs for deduplication
            "previously_discovered_jobs": self._load_previous_jobs(output_path)
        }
        
        return shared
    
    def _load_previous_jobs(self, output_path: str) -> List[Dict[str, Any]]:
        """Load previously discovered jobs for deduplication."""
        import json
        
        path = Path(output_path)
        if path.exists() and path.suffix == ".json":
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    return data.get("jobs", [])
            except Exception as e:
                logger.warning(f"Could not load previous jobs: {e}")
        
        return []


def create_default_root_urls(
    job_titles: List[str],
    location: str = "",
    remote_ok: bool = True
) -> List[str]:
    """Create default root URLs for common job boards.
    
    Args:
        job_titles: List of job titles to search for
        location: Location preference
        remote_ok: Whether to include remote jobs
        
    Returns:
        List of root URLs to start crawling
    """
    from urllib.parse import quote_plus
    
    root_urls = []
    
    # Prepare search terms
    primary_title = job_titles[0] if job_titles else "software engineer"
    encoded_title = quote_plus(primary_title)
    encoded_location = quote_plus(location) if location else ""
    
    # LinkedIn
    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
    if location:
        linkedin_url += f"&location={encoded_location}"
    if remote_ok:
        linkedin_url += "&f_WT=2"  # Remote filter
    root_urls.append(linkedin_url)
    
    # Indeed
    indeed_url = f"https://www.indeed.com/jobs?q={encoded_title}"
    if location:
        indeed_url += f"&l={encoded_location}"
    root_urls.append(indeed_url)
    
    # Glassdoor (note: may require more specific URL structure)
    glassdoor_url = f"https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={encoded_title}"
    if location:
        glassdoor_url += f"&locT=C&locId=1147401"  # Would need location ID mapping
    root_urls.append(glassdoor_url)
    
    # Wellfound (AngelList)
    wellfound_url = f"https://wellfound.com/jobs?q={encoded_title}"
    if remote_ok:
        wellfound_url += "&remote=true"
    root_urls.append(wellfound_url)
    
    return root_urls


def run_job_discovery(
    career_database_path: str,
    root_urls: Optional[List[str]] = None,
    search_preferences: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run the job discovery agent.
    
    Args:
        career_database_path: Path to the career database file
        root_urls: Optional list of URLs to crawl (will generate defaults if not provided)
        search_preferences: Search preferences (location, salary, etc.)
        config: Agent configuration options
        
    Returns:
        Results dictionary with discovered jobs and statistics
    """
    from utils.database_parser_v2 import load_career_database
    
    # Load career database
    career_db = load_career_database(career_database_path)
    
    # Generate root URLs if not provided
    if not root_urls:
        # Extract job titles from career database
        job_titles = []
        for exp in career_db.get("experiences", [])[:3]:  # Recent 3 roles
            if "title" in exp:
                job_titles.append(exp["title"])
        
        location = search_preferences.get("location", "") if search_preferences else ""
        remote_ok = search_preferences.get("remote_ok", True) if search_preferences else True
        
        root_urls = create_default_root_urls(job_titles, location, remote_ok)
        logger.info(f"Generated {len(root_urls)} default root URLs")
    
    # Create and run agent
    agent = JobDiscoveryAgent(config)
    shared = agent.prepare_shared_state(
        career_database=career_db,
        root_urls=root_urls,
        search_preferences=search_preferences
    )
    
    # Run the flow
    result = agent.run(shared)
    
    return {
        "success": shared.get("discovery_complete", False),
        "output_path": shared.get("output_path"),
        "summary_report": shared.get("summary_report"),
        "statistics": shared.get("job_discovery_stats"),
        "jobs_found": len(shared.get("unique_jobs", []))
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    config = {
        "max_pages_per_site": 50,
        "max_crawl_depth": 2,
        "min_relevance_score": 0.7,
        "extraction_batch_size": 5
    }
    
    # Example search preferences
    search_prefs = {
        "location": "San Francisco, CA",
        "remote_ok": True,
        "min_salary": 150000,
        "excluded_companies": ["Company1", "Company2"]
    }
    
    # Run discovery
    results = run_job_discovery(
        career_database_path="career_database.yaml",
        search_preferences=search_prefs,
        config=config
    )
    
    print(f"\nJob Discovery Complete!")
    print(f"Jobs found: {results['jobs_found']}")
    print(f"Results saved to: {results['output_path']}")