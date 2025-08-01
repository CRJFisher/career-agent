"""
Career Application Agent - Main Entry Point

This application helps automate job application customization by:
1. Extracting work experience from documents
2. Analyzing job requirements
3. Mapping experience to requirements
4. Generating tailored application documents

Built using PocketFlow's minimal LLM orchestration framework.
"""

import argparse
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

from flow import (
    ExperienceDatabaseFlow,
    RequirementExtractionFlow,
    AnalysisFlow,
    NarrativeFlow,
    GenerationFlow
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def build_career_database(config: Dict[str, Any]) -> Dict[str, Any]:
    """Build or update career database from documents."""
    logger.info("Building career database from documents...")
    
    shared = {
        "scan_config": config.get("document_sources", {})
    }
    
    flow = ExperienceDatabaseFlow()
    flow.run(shared)
    
    return shared.get("career_database", {})


def process_job_application(job_description: str, career_db: Dict[str, Any]) -> None:
    """Process a complete job application."""
    logger.info("Starting job application processing...")
    
    # Initialize shared store
    shared = {
        "job_description": job_description,
        "career_database": career_db
    }
    
    # Step 1: Extract requirements
    logger.info("Extracting job requirements...")
    req_flow = RequirementExtractionFlow()
    req_flow.run(shared)
    
    # Step 2: Analyze fit
    logger.info("Analyzing candidate fit...")
    analysis_flow = AnalysisFlow()
    result = analysis_flow.run(shared)
    
    if result == "pause":
        logger.info("Workflow paused for user review. Edit outputs/analysis_output.yaml and run with --resume")
        return
    
    # Step 3: Develop narrative (if not paused)
    logger.info("Developing narrative strategy...")
    narrative_flow = NarrativeFlow()
    result = narrative_flow.run(shared)
    
    if result == "pause":
        logger.info("Workflow paused for user review. Edit outputs/narrative_output.yaml and run with --resume")
        return
    
    # Step 4: Generate documents
    logger.info("Generating application documents...")
    gen_flow = GenerationFlow()
    gen_flow.run(shared)
    
    logger.info("Application processing complete!")


def resume_workflow(flow_name: str) -> None:
    """Resume a paused workflow from checkpoint."""
    logger.info(f"Resuming {flow_name} workflow...")
    
    # Load checkpoint will be handled by the flow
    shared = {}
    
    if flow_name == "analysis":
        # Resume from narrative flow
        narrative_flow = NarrativeFlow()
        narrative_flow.run(shared)
    elif flow_name == "narrative":
        # Resume from generation flow
        gen_flow = GenerationFlow()
        gen_flow.run(shared)
    else:
        logger.error(f"Unknown flow: {flow_name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Career Application Agent")
    parser.add_argument(
        "--build-db",
        action="store_true",
        help="Build career database from documents"
    )
    parser.add_argument(
        "--job-file",
        type=str,
        help="Path to job description file"
    )
    parser.add_argument(
        "--resume",
        type=str,
        choices=["analysis", "narrative"],
        help="Resume from a checkpoint"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    # Build career database if requested
    if args.build_db:
        career_db = build_career_database(config)
        db_path = Path("career_database.yaml")
        with open(db_path, 'w') as f:
            yaml.dump(career_db, f)
        logger.info(f"Career database saved to {db_path}")
        return
    
    # Resume workflow if requested
    if args.resume:
        resume_workflow(args.resume)
        return
    
    # Process job application
    if args.job_file:
        # Load career database
        db_path = Path("career_database.yaml")
        if not db_path.exists():
            logger.error("Career database not found. Run with --build-db first.")
            return
            
        with open(db_path, 'r') as f:
            career_db = yaml.safe_load(f)
            
        # Load job description
        with open(args.job_file, 'r') as f:
            job_description = f.read()
            
        process_job_application(job_description, career_db)
    else:
        # Demo mode
        logger.info("Running in demo mode...")
        demo_job = """
        Senior Software Engineer - AI/ML Platform
        
        We're looking for an experienced engineer to help build our ML platform.
        
        Requirements:
        - 5+ years Python experience
        - Experience with ML frameworks (PyTorch, TensorFlow)
        - Strong software engineering skills
        - Experience with distributed systems
        
        Nice to have:
        - Kubernetes experience
        - Cloud platforms (AWS, GCP)
        """
        
        demo_career_db = {
            "experience": [{
                "title": "Software Engineer",
                "company": "Tech Corp",
                "duration": "2020-2023",
                "technologies": ["Python", "PyTorch", "AWS"]
            }]
        }
        
        process_job_application(demo_job, demo_career_db)


if __name__ == "__main__":
    main()