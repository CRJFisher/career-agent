"""
Career Application Agent - Main Entry Point

This application helps automate job application customization by:
1. Loading career database from YAML
2. Extracting and analyzing job requirements
3. Researching the company (optional)
4. Assessing candidate suitability
5. Developing narrative strategy
6. Generating tailored CV and cover letter

Built using PocketFlow's minimal LLM orchestration framework.
"""

import argparse
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from flow import (
    ExperienceDatabaseFlow,
    RequirementExtractionFlow,
    AnalysisFlow,
    CompanyResearchAgent,
    AssessmentFlow,
    NarrativeFlow,
    GenerationFlow
)
from utils.database_parser import load_career_database

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


def initialize_shared_store(
    career_db: Dict[str, Any], 
    job_description: str,
    job_title: str,
    company_name: str,
    company_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize shared store with all required keys based on data contract.
    
    Returns:
        Complete shared store dictionary with all keys initialized
    """
    shared = {
        # Core inputs
        "career_db": career_db,
        "job_spec_text": job_description,
        "job_description": job_description,  # Alias for compatibility
        "job_title": job_title,
        "company_name": company_name,
        "company_url": company_url,
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        
        # Flow outputs (initialized as None/empty)
        "requirements": None,  # From RequirementExtractionFlow
        "requirement_mapping_raw": None,  # From RequirementMappingNode
        "requirement_mapping_assessed": None,  # From StrengthAssessmentNode
        "requirement_mapping_final": None,  # From GapAnalysisNode
        "gaps": None,  # From GapAnalysisNode
        "coverage_score": None,  # From GapAnalysisNode
        "company_research": None,  # From CompanyResearchAgent
        "suitability_assessment": None,  # From AssessmentFlow
        "prioritized_experiences": None,  # From ExperiencePrioritizationNode
        "narrative_strategy": None,  # From NarrativeStrategyNode
        "cv_markdown": None,  # From CVGenerationNode
        "cover_letter_text": None,  # From CoverLetterNode
        
        # Checkpoint management
        "checkpoint_data": {},
        
        # Configuration
        "enable_company_research": True,
        "max_research_iterations": 15,
        "enable_checkpoints": True
    }
    
    return shared


def process_job_application(
    job_description: str, 
    career_db: Dict[str, Any],
    job_title: str,
    company_name: str,
    company_url: Optional[str] = None,
    skip_company_research: bool = False
) -> Dict[str, Any]:
    """
    Process a complete job application through all flows.
    
    Args:
        job_description: Full text of job posting
        career_db: Parsed career database
        job_title: Position title
        company_name: Company name
        company_url: Optional company website URL
        skip_company_research: Whether to skip company research phase
        
    Returns:
        Final shared store with all generated materials
    """
    logger.info("=" * 60)
    logger.info("STARTING JOB APPLICATION PROCESSING")
    logger.info("=" * 60)
    logger.info(f"Position: {job_title} at {company_name}")
    logger.info("=" * 60)
    
    # Initialize shared store with complete data contract
    shared = initialize_shared_store(
        career_db=career_db,
        job_description=job_description,
        job_title=job_title,
        company_name=company_name,
        company_url=company_url
    )
    
    # Step 1: Extract requirements
    logger.info("\n[1/7] Extracting job requirements...")
    req_flow = RequirementExtractionFlow()
    req_flow.run(shared)
    
    if not shared.get("requirements"):
        logger.error("Failed to extract requirements")
        return shared
    
    # Step 2: Analyze fit (mapping, assessment, gaps)
    logger.info("\n[2/7] Analyzing candidate fit...")
    analysis_flow = AnalysisFlow()
    result = analysis_flow.run(shared)
    
    if result == "pause":
        logger.info("\n" + "=" * 60)
        logger.info("WORKFLOW PAUSED FOR REVIEW")
        logger.info("Edit outputs/analysis_output.yaml and run with --resume analysis")
        logger.info("=" * 60)
        return shared
    
    # Step 3: Company research (optional)
    if not skip_company_research and company_name:
        logger.info(f"\n[3/7] Researching {company_name}...")
        research_agent = CompanyResearchAgent(max_iterations=15)
        research_agent.run(shared)
    else:
        logger.info("\n[3/7] Skipping company research")
        shared["company_research"] = {}
    
    # Step 4: Suitability assessment
    logger.info("\n[4/7] Assessing overall suitability...")
    assessment_flow = AssessmentFlow()
    assessment_flow.run(shared)
    
    # Step 5: Develop narrative strategy
    logger.info("\n[5/7] Developing narrative strategy...")
    narrative_flow = NarrativeFlow()
    result = narrative_flow.run(shared)
    
    if result == "pause":
        logger.info("\n" + "=" * 60)
        logger.info("WORKFLOW PAUSED FOR REVIEW")
        logger.info("Edit outputs/narrative_output.yaml and run with --resume narrative")
        logger.info("=" * 60)
        return shared
    
    # Step 6: Generate documents
    logger.info("\n[6/7] Generating CV and cover letter...")
    gen_flow = GenerationFlow()
    gen_flow.run(shared)
    
    # Step 7: Export final materials
    logger.info("\n[7/7] Exporting final materials...")
    export_final_materials(shared)
    
    logger.info("\n" + "=" * 60)
    logger.info("APPLICATION PROCESSING COMPLETE!")
    logger.info("=" * 60)
    
    return shared


def export_final_materials(shared: Dict[str, Any]) -> None:
    """Export CV and cover letter to output files."""
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_title = shared.get("job_title", "position").replace(" ", "_").replace("/", "-")
    company = shared.get("company_name", "company").replace(" ", "_").replace("/", "-")
    
    # Export CV
    if shared.get("cv_markdown"):
        cv_filename = f"{timestamp}_{company}_{job_title}_CV.md"
        cv_path = output_dir / cv_filename
        cv_path.write_text(shared["cv_markdown"])
        logger.info(f"  ✓ CV saved: {cv_filename}")
        
        # Also save as PDF if pandoc is available
        try:
            import subprocess
            pdf_filename = cv_filename.replace(".md", ".pdf")
            pdf_path = output_dir / pdf_filename
            subprocess.run([
                "pandoc", str(cv_path), "-o", str(pdf_path),
                "--pdf-engine=xelatex"
            ], check=True, capture_output=True)
            logger.info(f"  ✓ PDF generated: {pdf_filename}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("  ℹ PDF generation skipped (pandoc not available)")
    
    # Export cover letter
    if shared.get("cover_letter_text"):
        letter_filename = f"{timestamp}_{company}_{job_title}_CoverLetter.txt"
        letter_path = output_dir / letter_filename
        letter_path.write_text(shared["cover_letter_text"])
        logger.info(f"  ✓ Cover letter saved: {letter_filename}")
        
        # Also save as DOCX for easy editing
        docx_filename = letter_filename.replace(".txt", ".docx")
        try:
            import subprocess
            docx_path = output_dir / docx_filename
            subprocess.run([
                "pandoc", str(letter_path), "-o", str(docx_path)
            ], check=True, capture_output=True)
            logger.info(f"  ✓ DOCX generated: {docx_filename}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass


def resume_workflow(flow_name: str, skip_company_research: bool = False) -> Dict[str, Any]:
    """
    Resume a paused workflow from checkpoint.
    
    Args:
        flow_name: Name of flow to resume from ("analysis" or "narrative")
        skip_company_research: Whether to skip company research when resuming
        
    Returns:
        Final shared store
    """
    logger.info("=" * 60)
    logger.info(f"RESUMING FROM {flow_name.upper()} CHECKPOINT")
    logger.info("=" * 60)
    
    # Load checkpoint data
    checkpoint_file = Path("outputs") / f"{flow_name}_output.yaml"
    if not checkpoint_file.exists():
        logger.error(f"Checkpoint file not found: {checkpoint_file}")
        logger.error("Make sure you've run the workflow and it created a checkpoint")
        return {}
    
    with open(checkpoint_file, 'r') as f:
        checkpoint_data = yaml.safe_load(f)
    
    # Initialize shared store from checkpoint
    shared = checkpoint_data.copy()
    
    # Ensure we have required fields for remaining flows
    if "current_date" not in shared:
        shared["current_date"] = datetime.now().strftime("%Y-%m-%d")
    
    if flow_name == "analysis":
        # Resume from company research (if enabled)
        if not skip_company_research and shared.get("company_name"):
            logger.info(f"\n[3/7] Researching {shared['company_name']}...")
            research_agent = CompanyResearchAgent(max_iterations=15)
            research_agent.run(shared)
        else:
            logger.info("\n[3/7] Skipping company research")
            shared["company_research"] = {}
        
        # Continue with assessment
        logger.info("\n[4/7] Assessing overall suitability...")
        assessment_flow = AssessmentFlow()
        assessment_flow.run(shared)
        
        # Continue with narrative
        logger.info("\n[5/7] Developing narrative strategy...")
        narrative_flow = NarrativeFlow()
        result = narrative_flow.run(shared)
        
        if result == "pause":
            logger.info("\n" + "=" * 60)
            logger.info("WORKFLOW PAUSED FOR REVIEW")
            logger.info("Edit outputs/narrative_output.yaml and run with --resume narrative")
            logger.info("=" * 60)
            return shared
        
        # Continue with generation
        logger.info("\n[6/7] Generating CV and cover letter...")
        gen_flow = GenerationFlow()
        gen_flow.run(shared)
        
        # Export materials
        logger.info("\n[7/7] Exporting final materials...")
        export_final_materials(shared)
        
    elif flow_name == "narrative":
        # Resume from generation only
        logger.info("\n[6/7] Generating CV and cover letter...")
        gen_flow = GenerationFlow()
        gen_flow.run(shared)
        
        # Export materials
        logger.info("\n[7/7] Exporting final materials...")
        export_final_materials(shared)
        
    else:
        logger.error(f"Unknown checkpoint name: {flow_name}")
        logger.error("Valid options are: 'analysis' or 'narrative'")
        return {}
    
    logger.info("\n" + "=" * 60)
    logger.info("APPLICATION PROCESSING COMPLETE!")
    logger.info("=" * 60)
    
    return shared


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Career Application Agent - Automate job application customization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build career database from documents
  python main.py --build-db
  
  # Process a job application
  python main.py --job-file job.txt --job-title "Senior Engineer" --company "TechCorp"
  
  # Resume from checkpoint
  python main.py --resume analysis
  
  # Skip company research for faster processing
  python main.py --job-file job.txt --job-title "Engineer" --company "StartupXYZ" --skip-research
        """
    )
    
    # Database building
    parser.add_argument(
        "--build-db",
        action="store_true",
        help="Build career database from documents"
    )
    
    # Job processing arguments
    parser.add_argument(
        "--job-file",
        type=str,
        help="Path to job description file"
    )
    parser.add_argument(
        "--job-title",
        type=str,
        help="Job title/position name"
    )
    parser.add_argument(
        "--company",
        type=str,
        help="Company name"
    )
    parser.add_argument(
        "--company-url",
        type=str,
        help="Company website URL (optional)"
    )
    parser.add_argument(
        "--career-db",
        type=str,
        default="career_database.yaml",
        help="Path to career database YAML file (default: career_database.yaml)"
    )
    
    # Resume from checkpoint
    parser.add_argument(
        "--resume",
        type=str,
        choices=["analysis", "narrative"],
        help="Resume from a checkpoint"
    )
    
    # Options
    parser.add_argument(
        "--skip-research",
        action="store_true",
        help="Skip company research phase"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Configuration file path"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with sample data"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config) if Path(args.config).exists() else {}
    
    # Build career database if requested
    if args.build_db:
        career_db = build_career_database(config)
        db_path = Path(args.career_db)
        with open(db_path, 'w') as f:
            yaml.dump(career_db, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Career database saved to {db_path}")
        return
    
    # Resume workflow if requested
    if args.resume:
        resume_workflow(args.resume, skip_company_research=args.skip_research)
        return
    
    # Demo mode
    if args.demo:
        logger.info("Running in demo mode...")
        demo_job = """
Senior Software Engineer - AI/ML Platform

We're looking for an experienced engineer to help build our next-generation ML platform.

Requirements:
- 5+ years of software engineering experience
- Strong Python programming skills
- Experience with ML frameworks (PyTorch, TensorFlow)
- Experience building scalable distributed systems
- Knowledge of cloud platforms (AWS, GCP, or Azure)
- Experience with containerization (Docker, Kubernetes)

Nice to have:
- Experience with MLOps practices
- Knowledge of data engineering pipelines
- Contributions to open source projects
- Experience mentoring junior engineers
"""
        
        demo_career_db = {
            "personal_info": {
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "(555) 123-4567",
                "location": "San Francisco, CA"
            },
            "experience": [{
                "title": "Senior Software Engineer",
                "company": "DataTech Inc",
                "duration": "2020-2023",
                "location": "San Francisco, CA",
                "description": "Led development of ML infrastructure serving 10M+ users",
                "achievements": [
                    "Built distributed training pipeline reducing model training time by 60%",
                    "Implemented real-time inference system handling 50K requests/second",
                    "Mentored team of 5 engineers on ML best practices"
                ],
                "technologies": ["Python", "PyTorch", "AWS", "Kubernetes", "Docker"]
            }],
            "education": [{
                "degree": "BS",
                "field": "Computer Science", 
                "institution": "UC Berkeley",
                "graduation_year": "2018"
            }],
            "skills": {
                "languages": ["Python", "Go", "JavaScript"],
                "ml_frameworks": ["PyTorch", "TensorFlow", "Scikit-learn"],
                "cloud": ["AWS", "GCP"],
                "tools": ["Docker", "Kubernetes", "Git"]
            }
        }
        
        process_job_application(
            job_description=demo_job,
            career_db=demo_career_db,
            job_title="Senior Software Engineer - AI/ML Platform",
            company_name="TechCorp",
            skip_company_research=args.skip_research
        )
        return
    
    # Process job application
    if args.job_file:
        # Validate required arguments
        if not args.job_title or not args.company:
            parser.error("--job-title and --company are required when using --job-file")
        
        # Load career database
        db_path = Path(args.career_db)
        if not db_path.exists():
            # Try loading from utils if it's a sample
            if args.career_db == "career_database.yaml":
                sample_path = Path("examples/sample_career_database.yaml")
                if sample_path.exists():
                    logger.info(f"Using sample career database from {sample_path}")
                    db_path = sample_path
                else:
                    logger.error(f"Career database not found: {args.career_db}")
                    logger.error("Run with --build-db first or specify --career-db path")
                    return
            else:
                logger.error(f"Career database not found: {args.career_db}")
                return
        
        # Load and parse career database
        try:
            career_db = load_career_database(db_path)
        except Exception as e:
            logger.error(f"Failed to load career database: {e}")
            return
            
        # Load job description
        job_path = Path(args.job_file)
        if not job_path.exists():
            logger.error(f"Job description file not found: {args.job_file}")
            return
            
        job_description = job_path.read_text()
        
        # Process application
        process_job_application(
            job_description=job_description,
            career_db=career_db,
            job_title=args.job_title,
            company_name=args.company,
            company_url=args.company_url,
            skip_company_research=args.skip_research
        )
    else:
        # Show help if no action specified
        parser.print_help()


if __name__ == "__main__":
    main()