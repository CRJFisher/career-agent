"""Job Discovery Agent Nodes

This module contains specialized nodes for autonomous job discovery across multiple job boards.
These nodes work together to crawl job boards, extract listings, and filter based on relevance.
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin, parse_qs
import hashlib

from nodes import Node
from utils.llm_wrapper import LLMWrapper
from utils.ai_browser import AIBrowser, AISimpleScraper
from utils.database_parser_v2 import CareerDatabaseParser

logger = logging.getLogger(__name__)


class InitializeSearchNode(Node):
    """Initialize job search parameters from career profile and user preferences."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare search initialization data."""
        return {
            "career_database": shared.get("career_database", {}),
            "search_preferences": shared.get("search_preferences", {}),
            "root_urls": shared.get("root_urls", []),
            "max_depth": shared.get("max_crawl_depth", 3),
            "max_pages": shared.get("max_pages_per_site", 100)
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Extract search parameters from career profile."""
        career_db = prep_res["career_database"]
        preferences = prep_res["search_preferences"]
        
        # Extract key skills and titles from career database
        skills = set()
        job_titles = set()
        
        # Get skills from database
        if "skills" in career_db:
            for skill_type, skill_list in career_db["skills"].items():
                if isinstance(skill_list, list):
                    skills.update(skill_list)
        
        # Get job titles from experiences
        for exp in career_db.get("experiences", []):
            if "title" in exp:
                job_titles.add(exp["title"])
        
        # Build search parameters
        search_params = {
            "keywords": list(skills)[:10],  # Top 10 skills
            "job_titles": list(job_titles),
            "location": preferences.get("location", ""),
            "remote_ok": preferences.get("remote", True),
            "experience_level": self._determine_experience_level(career_db),
            "industry_preferences": preferences.get("industries", []),
            "company_size": preferences.get("company_size", "any"),
            "min_salary": preferences.get("min_salary"),
            "excluded_companies": preferences.get("excluded_companies", [])
        }
        
        # Enhance root URLs with search parameters if not already present
        enhanced_urls = []
        for url in prep_res["root_urls"]:
            if "linkedin.com" in url and "keywords=" not in url:
                # Add keywords to LinkedIn URL
                keywords = "+".join(search_params["keywords"][:3])
                enhanced_url = f"{url}?keywords={keywords}"
                if search_params["location"]:
                    enhanced_url += f"&location={search_params['location']}"
                enhanced_urls.append(enhanced_url)
            else:
                enhanced_urls.append(url)
        
        return {
            "search_params": search_params,
            "root_urls": enhanced_urls,
            "crawl_config": {
                "max_depth": prep_res["max_depth"],
                "max_pages": prep_res["max_pages"],
                "respect_robots": True,
                "delay_between_requests": 2.0,  # Polite crawling
                "user_agent": "CareerAgent/1.0 (Job Discovery Bot)"
            }
        }
    
    def _determine_experience_level(self, career_db: Dict[str, Any]) -> str:
        """Determine experience level from career database."""
        total_years = 0
        
        for exp in career_db.get("experiences", []):
            period = exp.get("period", "")
            # Simple year extraction - could be enhanced
            years_match = re.findall(r"(\d{4})", period)
            if len(years_match) >= 2:
                start_year = int(years_match[0])
                end_year = int(years_match[-1]) if years_match[-1] != str(datetime.now().year) else datetime.now().year
                total_years += (end_year - start_year)
        
        if total_years < 2:
            return "entry"
        elif total_years < 5:
            return "mid"
        elif total_years < 10:
            return "senior"
        else:
            return "executive"
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Store search parameters in shared state."""
        shared["search_params"] = exec_res["search_params"]
        shared["enhanced_root_urls"] = exec_res["root_urls"]
        shared["crawl_config"] = exec_res["crawl_config"]
        shared["discovered_urls"] = set()  # Track all discovered URLs
        shared["job_listings"] = []  # Store extracted jobs
        
        logger.info(f"Initialized search with {len(exec_res['root_urls'])} root URLs")
        logger.info(f"Search keywords: {exec_res['search_params']['keywords'][:5]}")
        
        return "search_initialized"


class CrawlJobBoardNode(Node):
    """Crawl job boards to discover job listing URLs."""
    
    def __init__(self):
        super().__init__()
        self.visited_urls = set()
        self.job_patterns = {
            "linkedin": [
                r"/jobs/view/\d+",
                r"/jobs/collections/",
                r"/jobs/search/"
            ],
            "indeed": [
                r"/viewjob\?jk=",
                r"/rc/clk\?jk=",
                r"/jobs\?"
            ],
            "glassdoor": [
                r"/job-listing/.*-JV_",
                r"/Jobs/.*-jobs-"
            ],
            "wellfound": [
                r"/jobs/\d+",
                r"/company/.*/jobs/"
            ]
        }
    
    def prep(self, shared: dict) -> dict:
        """Prepare crawling data."""
        return {
            "root_urls": shared.get("enhanced_root_urls", []),
            "crawl_config": shared.get("crawl_config", {}),
            "discovered_urls": shared.get("discovered_urls", set()),
            "current_depth": shared.get("current_crawl_depth", 0)
        }
    
    async def exec_async(self, prep_res: dict) -> dict:
        """Execute crawling asynchronously."""
        scraper = AISimpleScraper()
        discovered_jobs = []
        crawl_queue = [(url, 0) for url in prep_res["root_urls"]]  # (url, depth)
        pages_crawled = 0
        max_pages = prep_res["crawl_config"].get("max_pages", 100)
        max_depth = prep_res["crawl_config"].get("max_depth", 3)
        
        while crawl_queue and pages_crawled < max_pages:
            url, depth = crawl_queue.pop(0)
            
            # Skip if already visited or too deep
            if url in self.visited_urls or depth > max_depth:
                continue
            
            self.visited_urls.add(url)
            pages_crawled += 1
            
            try:
                # Respect crawl delay
                await asyncio.sleep(prep_res["crawl_config"].get("delay_between_requests", 2.0))
                
                # Extract content and links
                logger.info(f"Crawling {url} (depth: {depth})")
                content = await scraper.extract_content(
                    url,
                    include_links=True,
                    wait_for_js=True
                )
                
                if content.get("success"):
                    # Find job listing URLs
                    links = content.get("links", [])
                    base_domain = urlparse(url).netloc
                    
                    for link in links:
                        # Normalize URL
                        full_url = urljoin(url, link)
                        
                        # Check if it's a job listing URL
                        if self._is_job_listing_url(full_url, base_domain):
                            if full_url not in prep_res["discovered_urls"]:
                                discovered_jobs.append({
                                    "url": full_url,
                                    "source_page": url,
                                    "discovered_at": datetime.now().isoformat(),
                                    "board": self._identify_job_board(full_url)
                                })
                                prep_res["discovered_urls"].add(full_url)
                        
                        # Add to crawl queue if it's a search/listing page
                        elif self._is_search_page(full_url, base_domain) and depth < max_depth:
                            if full_url not in self.visited_urls:
                                crawl_queue.append((full_url, depth + 1))
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue
        
        return {
            "discovered_jobs": discovered_jobs,
            "pages_crawled": pages_crawled,
            "total_discovered": len(discovered_jobs)
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Synchronous wrapper for async execution."""
        return asyncio.run(self.exec_async(prep_res))
    
    def _is_job_listing_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is likely a job listing."""
        # Check against known patterns
        for board, patterns in self.job_patterns.items():
            if board in base_domain:
                for pattern in patterns:
                    if re.search(pattern, url) and "search" not in url.lower():
                        return True
        
        # Generic job URL patterns
        generic_patterns = [
            r"/job/\d+",
            r"/position/\d+",
            r"/opening/\d+",
            r"/career/\d+",
            r"/opportunity/\d+"
        ]
        
        for pattern in generic_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def _is_search_page(self, url: str, base_domain: str) -> bool:
        """Check if URL is a search or listing page worth crawling."""
        search_indicators = [
            "search", "jobs", "careers", "openings", "positions",
            "page=", "offset=", "start=", "from="
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in search_indicators)
    
    def _identify_job_board(self, url: str) -> str:
        """Identify which job board the URL is from."""
        domain = urlparse(url).netloc.lower()
        
        if "linkedin.com" in domain:
            return "linkedin"
        elif "indeed.com" in domain:
            return "indeed"
        elif "glassdoor.com" in domain:
            return "glassdoor"
        elif "wellfound.com" in domain or "angel.co" in domain:
            return "wellfound"
        else:
            return "other"
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Update shared state with discovered jobs."""
        # Add to existing discovered jobs
        existing_jobs = shared.get("discovered_job_urls", [])
        existing_jobs.extend(exec_res["discovered_jobs"])
        shared["discovered_job_urls"] = existing_jobs
        
        logger.info(f"Discovered {exec_res['total_discovered']} new job URLs")
        logger.info(f"Total pages crawled: {exec_res['pages_crawled']}")
        
        return "jobs_discovered"


class ExtractJobListingsNode(Node):
    """Extract detailed job information from discovered URLs."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare job extraction data."""
        return {
            "discovered_jobs": shared.get("discovered_job_urls", []),
            "extraction_batch_size": shared.get("extraction_batch_size", 10),
            "search_params": shared.get("search_params", {})
        }
    
    async def exec_async(self, prep_res: dict) -> dict:
        """Extract job details asynchronously."""
        llm_wrapper = LLMWrapper()
        scraper = AISimpleScraper()
        extracted_jobs = []
        
        # Process in batches
        batch_size = prep_res["extraction_batch_size"]
        jobs_to_process = prep_res["discovered_jobs"][:50]  # Limit for demo
        
        for i in range(0, len(jobs_to_process), batch_size):
            batch = jobs_to_process[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self._extract_single_job(job, scraper, llm_wrapper) for job in batch],
                return_exceptions=True
            )
            
            for job_info, result in zip(batch, batch_results):
                if isinstance(result, dict) and result.get("success"):
                    result["source_url"] = job_info["url"]
                    result["job_board"] = job_info["board"]
                    result["discovered_at"] = job_info["discovered_at"]
                    extracted_jobs.append(result)
                else:
                    logger.error(f"Failed to extract {job_info['url']}: {result}")
        
        return {
            "extracted_jobs": extracted_jobs,
            "extraction_success_rate": len(extracted_jobs) / len(jobs_to_process) if jobs_to_process else 0
        }
    
    async def _extract_single_job(self, job_info: Dict[str, Any], scraper: AISimpleScraper, 
                                  llm_wrapper: LLMWrapper) -> Dict[str, Any]:
        """Extract details from a single job posting."""
        try:
            # Get page content
            content = await scraper.extract_content(
                job_info["url"],
                wait_for_js=True,
                include_metadata=True
            )
            
            if not content.get("success"):
                return {"success": False, "error": "Failed to load page"}
            
            # Use LLM to extract structured data
            extraction_prompt = f"""
            Extract the following information from this job posting:
            
            {content.get('text', '')[:4000]}
            
            Extract:
            1. Job title
            2. Company name
            3. Location (city, state/country, remote options)
            4. Salary range (if mentioned)
            5. Required skills (list)
            6. Nice-to-have skills (list)
            7. Years of experience required
            8. Education requirements
            9. Job type (full-time, part-time, contract, etc.)
            10. Application deadline (if mentioned)
            11. Key responsibilities (top 5)
            12. Company benefits (if mentioned)
            13. Team size (if mentioned)
            14. Tech stack (if mentioned)
            
            Return as a structured JSON object. Use null for missing information.
            """
            
            extracted_data = await llm_wrapper.call_llm(
                extraction_prompt,
                response_format="json",
                max_tokens=1500
            )
            
            # Parse the response
            if isinstance(extracted_data, str):
                try:
                    extracted_data = json.loads(extracted_data)
                except:
                    logger.error(f"Failed to parse LLM response for {job_info['url']}")
                    return {"success": False, "error": "Invalid LLM response"}
            
            return {
                "success": True,
                "job_data": extracted_data,
                "page_title": content.get("metadata", {}).get("title", ""),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting job {job_info['url']}: {e}")
            return {"success": False, "error": str(e)}
    
    def exec(self, prep_res: dict) -> dict:
        """Synchronous wrapper for async execution."""
        return asyncio.run(self.exec_async(prep_res))
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Store extracted jobs in shared state."""
        shared["extracted_jobs"] = exec_res["extracted_jobs"]
        
        logger.info(f"Extracted {len(exec_res['extracted_jobs'])} job details")
        logger.info(f"Extraction success rate: {exec_res['extraction_success_rate']:.2%}")
        
        return "jobs_extracted"


class FilterRelevantJobsNode(Node):
    """Score and filter jobs based on relevance to career profile."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare filtering data."""
        return {
            "extracted_jobs": shared.get("extracted_jobs", []),
            "career_database": shared.get("career_database", {}),
            "search_params": shared.get("search_params", {}),
            "min_relevance_score": shared.get("min_relevance_score", 0.6)
        }
    
    async def exec_async(self, prep_res: dict) -> dict:
        """Score jobs for relevance asynchronously."""
        llm_wrapper = LLMWrapper()
        scored_jobs = []
        
        # Create career summary for scoring
        career_summary = self._create_career_summary(prep_res["career_database"])
        
        # Score each job
        for job in prep_res["extracted_jobs"]:
            score = await self._score_job_relevance(
                job,
                career_summary,
                prep_res["search_params"],
                llm_wrapper
            )
            
            if score["overall_score"] >= prep_res["min_relevance_score"]:
                job["relevance_score"] = score
                scored_jobs.append(job)
        
        # Sort by relevance
        scored_jobs.sort(key=lambda x: x["relevance_score"]["overall_score"], reverse=True)
        
        return {
            "relevant_jobs": scored_jobs,
            "total_filtered": len(prep_res["extracted_jobs"]) - len(scored_jobs),
            "avg_relevance_score": sum(j["relevance_score"]["overall_score"] for j in scored_jobs) / len(scored_jobs) if scored_jobs else 0
        }
    
    async def _score_job_relevance(self, job: Dict[str, Any], career_summary: str,
                                   search_params: Dict[str, Any], llm_wrapper: LLMWrapper) -> Dict[str, Any]:
        """Score a single job for relevance."""
        scoring_prompt = f"""
        Score this job's relevance to the candidate's profile.
        
        CANDIDATE PROFILE:
        {career_summary}
        
        SEARCH PREFERENCES:
        - Preferred location: {search_params.get('location', 'Any')}
        - Remote OK: {search_params.get('remote_ok', True)}
        - Min salary: {search_params.get('min_salary', 'Not specified')}
        - Experience level: {search_params.get('experience_level', 'Not specified')}
        
        JOB DETAILS:
        {json.dumps(job.get('job_data', {}), indent=2)}
        
        Score the following aspects (0.0 to 1.0):
        1. skills_match: How well do required skills match candidate's skills?
        2. experience_match: Does experience level align?
        3. location_match: Does location/remote work?
        4. career_progression: Is this a logical next step?
        5. culture_fit: Based on company info, likely culture fit?
        
        Also provide:
        - overall_score: Weighted average (skills 40%, experience 25%, location 15%, progression 15%, culture 5%)
        - key_strengths: Top 3 reasons this is a good match
        - concerns: Any red flags or mismatches
        - recommendation: "strong_match", "good_match", "possible_match", or "poor_match"
        
        Return as JSON.
        """
        
        try:
            score_data = await llm_wrapper.call_llm(
                scoring_prompt,
                response_format="json",
                max_tokens=800
            )
            
            if isinstance(score_data, str):
                score_data = json.loads(score_data)
            
            return score_data
            
        except Exception as e:
            logger.error(f"Error scoring job: {e}")
            # Return default low score on error
            return {
                "overall_score": 0.3,
                "skills_match": 0.3,
                "experience_match": 0.3,
                "location_match": 0.3,
                "career_progression": 0.3,
                "culture_fit": 0.3,
                "key_strengths": [],
                "concerns": ["Failed to analyze"],
                "recommendation": "poor_match"
            }
    
    def _create_career_summary(self, career_db: Dict[str, Any]) -> str:
        """Create a concise career summary for scoring."""
        summary_parts = []
        
        # Current/recent role
        if career_db.get("experiences"):
            recent_exp = career_db["experiences"][0]
            summary_parts.append(f"Current/Recent: {recent_exp.get('title', 'Unknown')} at {recent_exp.get('company', 'Unknown')}")
        
        # Total experience
        total_years = 0
        for exp in career_db.get("experiences", []):
            period = exp.get("period", "")
            years_match = re.findall(r"(\d{4})", period)
            if len(years_match) >= 2:
                total_years += int(years_match[-1]) - int(years_match[0])
        summary_parts.append(f"Total Experience: ~{total_years} years")
        
        # Key skills
        all_skills = []
        if "skills" in career_db:
            for skill_type, skills in career_db["skills"].items():
                if isinstance(skills, list):
                    all_skills.extend(skills[:5])  # Top 5 from each category
        summary_parts.append(f"Key Skills: {', '.join(all_skills[:10])}")
        
        # Education
        if career_db.get("education"):
            education = career_db["education"][0]
            summary_parts.append(f"Education: {education.get('degree', 'Unknown')} from {education.get('institution', 'Unknown')}")
        
        return "\n".join(summary_parts)
    
    def exec(self, prep_res: dict) -> dict:
        """Synchronous wrapper for async execution."""
        return asyncio.run(self.exec_async(prep_res))
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Store filtered jobs in shared state."""
        shared["relevant_jobs"] = exec_res["relevant_jobs"]
        shared["job_discovery_stats"] = {
            "total_discovered": len(shared.get("discovered_job_urls", [])),
            "total_extracted": len(shared.get("extracted_jobs", [])),
            "total_relevant": len(exec_res["relevant_jobs"]),
            "avg_relevance_score": exec_res["avg_relevance_score"]
        }
        
        logger.info(f"Found {len(exec_res['relevant_jobs'])} relevant jobs")
        logger.info(f"Filtered out {exec_res['total_filtered']} jobs below threshold")
        
        return "jobs_filtered"


class DeduplicateJobsNode(Node):
    """Remove duplicate job listings across different sources."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare deduplication data."""
        return {
            "relevant_jobs": shared.get("relevant_jobs", []),
            "existing_jobs": shared.get("previously_discovered_jobs", [])
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Deduplicate jobs based on multiple factors."""
        seen_jobs = set()
        unique_jobs = []
        duplicates_removed = 0
        
        # Build hashes for existing jobs
        for job in prep_res["existing_jobs"]:
            job_hash = self._create_job_hash(job)
            seen_jobs.add(job_hash)
        
        # Process new jobs
        for job in prep_res["relevant_jobs"]:
            job_hash = self._create_job_hash(job)
            
            if job_hash not in seen_jobs:
                seen_jobs.add(job_hash)
                unique_jobs.append(job)
            else:
                duplicates_removed += 1
                logger.debug(f"Duplicate job removed: {job.get('job_data', {}).get('title', 'Unknown')}")
        
        return {
            "unique_jobs": unique_jobs,
            "duplicates_removed": duplicates_removed
        }
    
    def _create_job_hash(self, job: Dict[str, Any]) -> str:
        """Create a hash to identify unique jobs."""
        job_data = job.get("job_data", {})
        
        # Combine key fields for uniqueness
        unique_string = f"{job_data.get('company', '').lower()}"
        unique_string += f"{job_data.get('title', '').lower()}"
        unique_string += f"{job_data.get('location', '').lower()}"
        
        # Also consider the job board and any unique ID
        unique_string += job.get("job_board", "")
        
        # Extract any job ID from URL
        url = job.get("source_url", "")
        job_id_match = re.search(r"/(\d{5,})", url)
        if job_id_match:
            unique_string += job_id_match.group(1)
        
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Update shared state with deduplicated jobs."""
        shared["unique_jobs"] = exec_res["unique_jobs"]
        shared["deduplication_stats"] = {
            "duplicates_removed": exec_res["duplicates_removed"],
            "unique_jobs_count": len(exec_res["unique_jobs"])
        }
        
        logger.info(f"Deduplication complete: {exec_res['duplicates_removed']} duplicates removed")
        logger.info(f"Unique jobs remaining: {len(exec_res['unique_jobs'])}")
        
        return "jobs_deduplicated"


class SaveJobsNode(Node):
    """Save discovered jobs to database and generate reports."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare job saving data."""
        return {
            "unique_jobs": shared.get("unique_jobs", []),
            "output_format": shared.get("output_format", "json"),
            "output_path": shared.get("output_path", "discovered_jobs.json"),
            "discovery_stats": shared.get("job_discovery_stats", {})
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Save jobs in requested format."""
        jobs = prep_res["unique_jobs"]
        output_path = prep_res["output_path"]
        
        # Add metadata
        output_data = {
            "discovery_timestamp": datetime.now().isoformat(),
            "total_jobs": len(jobs),
            "statistics": prep_res["discovery_stats"],
            "jobs": jobs
        }
        
        # Save based on format
        if prep_res["output_format"] == "json":
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
        
        elif prep_res["output_format"] == "csv":
            # Flatten job data for CSV
            import csv
            csv_path = output_path.replace(".json", ".csv")
            
            with open(csv_path, "w", newline="") as f:
                if jobs:
                    # Create fieldnames from first job
                    fieldnames = ["source_url", "job_board", "relevance_score", "recommendation"]
                    job_data_fields = list(jobs[0].get("job_data", {}).keys())
                    fieldnames.extend(job_data_fields)
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for job in jobs:
                        row = {
                            "source_url": job.get("source_url", ""),
                            "job_board": job.get("job_board", ""),
                            "relevance_score": job.get("relevance_score", {}).get("overall_score", 0),
                            "recommendation": job.get("relevance_score", {}).get("recommendation", "")
                        }
                        row.update(job.get("job_data", {}))
                        writer.writerow(row)
        
        # Generate summary report
        summary = self._generate_summary_report(jobs, prep_res["discovery_stats"])
        
        return {
            "output_path": output_path,
            "jobs_saved": len(jobs),
            "summary_report": summary
        }
    
    def _generate_summary_report(self, jobs: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Generate a human-readable summary report."""
        report_lines = [
            "=== Job Discovery Summary ===",
            f"Discovery Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "Statistics:",
            f"- Total URLs Discovered: {stats.get('total_discovered', 0)}",
            f"- Jobs Successfully Extracted: {stats.get('total_extracted', 0)}",
            f"- Jobs Meeting Relevance Threshold: {stats.get('total_relevant', 0)}",
            f"- Average Relevance Score: {stats.get('avg_relevance_score', 0):.2%}",
            "",
            "Top 10 Opportunities:"
        ]
        
        # Add top jobs
        for i, job in enumerate(jobs[:10], 1):
            job_data = job.get("job_data", {})
            score = job.get("relevance_score", {})
            
            report_lines.extend([
                f"\n{i}. {job_data.get('title', 'Unknown Title')} at {job_data.get('company', 'Unknown Company')}",
                f"   Location: {job_data.get('location', 'Not specified')}",
                f"   Relevance: {score.get('overall_score', 0):.2%} ({score.get('recommendation', 'Unknown')})",
                f"   Key Match: {', '.join(score.get('key_strengths', [])[:2])}",
                f"   URL: {job.get('source_url', 'N/A')}"
            ])
        
        return "\n".join(report_lines)
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Finalize job discovery process."""
        shared["discovery_complete"] = True
        shared["output_path"] = exec_res["output_path"]
        shared["summary_report"] = exec_res["summary_report"]
        
        # Save summary to file
        summary_path = exec_res["output_path"].replace(".json", "_summary.txt")
        with open(summary_path, "w") as f:
            f.write(exec_res["summary_report"])
        
        logger.info(f"Saved {exec_res['jobs_saved']} jobs to {exec_res['output_path']}")
        logger.info(f"Summary report saved to {summary_path}")
        
        # Print summary to console
        print("\n" + exec_res["summary_report"])
        
        return "discovery_complete"