"""
Main orchestrator for the PocketFlow career application agent.

This is the entry point that coordinates all flows to process job applications.

Note: PocketFlow is implemented directly in this project following the minimalist
philosophy of The-Pocket/PocketFlow - a 100-line LLM orchestration framework.
Core components are in nodes.py (Nodes), flow.py (Flows), and shared store pattern.
"""

import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from flow import Flow
from nodes import Node


class MainOrchestrator:
    """
    Main orchestrator that coordinates all sub-flows for job application processing.
    
    This class manages the high-level workflow:
    1. Extract requirements from job description
    2. Analyze candidate fit
    3. Research company (if needed)
    4. Assess overall suitability
    5. Develop narrative strategy
    6. Generate application documents
    """
    
    def __init__(self, career_db_path: Path, output_dir: Path):
        self.career_db_path = career_db_path
        self.output_dir = output_dir
        self.shared_store = {
            'career_db_path': career_db_path,
            'output_dir': output_dir
        }
    
    async def process_application(self, job_description: str, company_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a job application end-to-end.
        
        Args:
            job_description: The job description text
            company_url: Optional company website URL for research
            
        Returns:
            Dictionary containing generated CV, cover letter, and analysis results
        """
        # Initialize shared store with job information
        self.shared_store['job_description'] = job_description
        self.shared_store['company_url'] = company_url
        
        # TODO: Execute flows in sequence
        # 1. RequirementExtractionFlow
        # 2. AnalysisFlow
        # 3. CompanyResearchFlow (if company_url provided)
        # 4. AssessmentFlow
        # 5. NarrativeFlow
        # 6. GenerationFlow
        
        return self.shared_store


def main():
    """Command-line interface for the career application agent."""
    parser = argparse.ArgumentParser(
        description='PocketFlow Career Application Agent - Automates job application customization'
    )
    parser.add_argument(
        'job_description',
        type=str,
        help='Path to job description file or job description text'
    )
    parser.add_argument(
        '--career-db',
        type=Path,
        required=True,
        help='Path to career database YAML file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('./output'),
        help='Directory for generated documents (default: ./output)'
    )
    parser.add_argument(
        '--company-url',
        type=str,
        help='Company website URL for additional research'
    )
    
    args = parser.parse_args()
    
    # Read job description
    if Path(args.job_description).exists():
        with open(args.job_description, 'r') as f:
            job_description = f.read()
    else:
        job_description = args.job_description
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run orchestrator
    orchestrator = MainOrchestrator(args.career_db, args.output_dir)
    
    # Run async process
    result = asyncio.run(
        orchestrator.process_application(job_description, args.company_url)
    )
    
    print(f"Application documents generated in: {args.output_dir}")
    return 0


if __name__ == '__main__':
    exit(main())