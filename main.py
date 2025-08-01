"""
Main orchestrator for the PocketFlow career application agent.

This is the entry point that coordinates all flows to process job applications.
Following PocketFlow patterns, flows are connected and executed through a
shared store that maintains state across the entire application process.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import flows
from flow import (
    Flow,
    RequirementExtractionFlow,
    AnalysisFlow,
    CompanyResearchFlow,
    AssessmentFlow,
    NarrativeFlow,
    GenerationFlow
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApplicationOrchestrator(Flow):
    """
    Main orchestrator flow that coordinates all sub-flows for job application processing.
    
    This is implemented as a Flow itself, allowing it to be composed with other flows
    and maintain the same execution pattern.
    """
    
    def __init__(self):
        # Create all sub-flows
        self.requirement_flow = RequirementExtractionFlow()
        self.analysis_flow = AnalysisFlow()
        self.research_flow = CompanyResearchFlow()
        self.assessment_flow = AssessmentFlow()
        self.narrative_flow = NarrativeFlow()
        self.generation_flow = GenerationFlow()
        
        # Connect flows in sequence
        # Requirement extraction must succeed to continue
        self.requirement_flow - "success" >> self.analysis_flow
        
        # After analysis, always do research (if URL provided)
        self.analysis_flow >> self.research_flow
        
        # After research (or skipping it), assess suitability
        self.research_flow >> self.assessment_flow
        
        # After assessment, develop narrative
        self.assessment_flow >> self.narrative_flow
        
        # Finally generate documents
        self.narrative_flow >> self.generation_flow
        
        # Initialize with requirement extraction as start
        super().__init__(start=self.requirement_flow, name="ApplicationOrchestrator")
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any) -> Optional[str]:
        """Check if application processing completed successfully."""
        if shared.get('flow_error'):
            logger.error(f"Application processing failed: {shared['flow_error']}")
            return "error"
        
        # Check if we have generated documents
        if shared.get('cv_generated') and shared.get('cover_letter_generated'):
            logger.info("Application documents generated successfully")
            return "success"
        else:
            logger.warning("Application processing completed but documents not generated")
            return "incomplete"


def load_career_database(db_path: Path) -> Dict[str, Any]:
    """Load and parse the career database YAML file."""
    try:
        from utils.database_parser import CareerDatabaseParser
        parser = CareerDatabaseParser()
        return parser.parse(str(db_path))
    except Exception as e:
        logger.error(f"Failed to load career database: {e}")
        raise


def save_outputs(shared: Dict[str, Any], output_dir: Path) -> None:
    """Save generated documents and analysis results to output directory."""
    import json
    import yaml
    
    # Save extracted requirements
    if shared.get('job_requirements_structured'):
        req_path = output_dir / 'extracted_requirements.yaml'
        with open(req_path, 'w') as f:
            yaml.dump(shared['job_requirements_structured'], f, default_flow_style=False)
        logger.info(f"Saved extracted requirements to {req_path}")
    
    # Save analysis results
    analysis_data = {
        'strengths': shared.get('strengths_analysis', {}),
        'gaps': shared.get('gaps_analysis', {}),
        'suitability_score': shared.get('suitability_score', 0),
        'narrative_strategy': shared.get('narrative_strategy', {})
    }
    
    if any(analysis_data.values()):
        analysis_path = output_dir / 'analysis_results.json'
        with open(analysis_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        logger.info(f"Saved analysis results to {analysis_path}")
    
    # Save generated CV
    if shared.get('generated_cv'):
        cv_path = output_dir / 'generated_cv.md'
        with open(cv_path, 'w') as f:
            f.write(shared['generated_cv'])
        logger.info(f"Saved generated CV to {cv_path}")
    
    # Save generated cover letter
    if shared.get('generated_cover_letter'):
        letter_path = output_dir / 'generated_cover_letter.md'
        with open(letter_path, 'w') as f:
            f.write(shared['generated_cover_letter'])
        logger.info(f"Saved generated cover letter to {letter_path}")


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
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Read job description
    if Path(args.job_description).exists():
        logger.info(f"Reading job description from file: {args.job_description}")
        with open(args.job_description, 'r') as f:
            job_description = f.read()
    else:
        logger.info("Using provided text as job description")
        job_description = args.job_description
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {args.output_dir}")
    
    # Load career database
    logger.info(f"Loading career database from: {args.career_db}")
    career_data = load_career_database(args.career_db)
    
    # Initialize shared store
    shared_store = {
        'job_description': job_description,
        'career_database': career_data,
        'company_url': args.company_url,
        'output_dir': str(args.output_dir)
    }
    
    # Create and run the orchestrator
    logger.info("Starting application processing...")
    orchestrator = ApplicationOrchestrator()
    
    # Optionally visualize the flow
    if args.debug:
        print("\n" + orchestrator.visualize() + "\n")
    
    try:
        # Run the orchestrator
        final_action = orchestrator.run(shared_store)
        
        # Save outputs
        save_outputs(shared_store, args.output_dir)
        
        if final_action == "success":
            print(f"\n✅ Application documents generated successfully in: {args.output_dir}")
            return 0
        else:
            print(f"\n⚠️  Application processing completed with status: {final_action}")
            return 1
            
    except Exception as e:
        logger.error(f"Application processing failed: {e}")
        print(f"\n❌ Error: {e}")
        return 2


if __name__ == '__main__':
    exit(main())