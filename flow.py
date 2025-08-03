"""
Career application agent flows.

This module implements the application-specific flows that orchestrate nodes
for the career application system. Each flow represents a complete workflow
or pipeline in the job application process.

All flows extend PocketFlow's base Flow class.
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from pathlib import Path
from pocketflow import Flow, BatchFlow
from nodes import (
    ExtractRequirementsNode,
    RequirementMappingNode,
    StrengthAssessmentNode,
    GapAnalysisNode,
    SaveCheckpointNode,
    LoadCheckpointNode,
    ScanDocumentsNode,
    ExtractExperienceNode,
    BuildDatabaseNode,
    DecideActionNode,
    WebSearchNode,
    ReadContentNode,
    SynthesizeInfoNode,
    SuitabilityScoringNode,
    ExperiencePrioritizationNode,
    NarrativeStrategyNode,
    CVGenerationNode,
    CoverLetterNode
)

logger = logging.getLogger(__name__)


class RequirementExtractionFlow(Flow):
    """
    Extracts and structures job requirements from a job description.
    
    This simple flow takes a job description and produces structured
    requirements in YAML format.
    """
    
    def __init__(self):
        # Create and connect nodes
        extract = ExtractRequirementsNode()
        
        # Initialize with start node
        super().__init__(start=extract)


class AnalysisFlow(Flow):
    """
    Analyzes candidate fit by mapping requirements to experience.
    
    This flow performs a complete analysis pipeline:
    1. Maps job requirements to career database evidence
    2. Assesses the strength of each mapping (HIGH/MEDIUM/LOW)
    3. Identifies gaps and generates mitigation strategies
    4. Saves checkpoint for user review
    
    The flow pauses after saving the checkpoint, allowing users to review
    and edit the analysis before proceeding to narrative generation.
    """
    
    def __init__(self):
        # Create nodes
        mapping = RequirementMappingNode()
        assessment = StrengthAssessmentNode()
        gap_analysis = GapAnalysisNode()
        checkpoint = SaveCheckpointNode()
        
        # Configure checkpoint to save analysis results
        checkpoint.set_params({
            "flow_name": "analysis",
            "checkpoint_data": [
                "requirements",
                "requirement_mapping_raw",
                "requirement_mapping_assessed",
                "requirement_mapping_final",
                "gaps",
                "coverage_score"
            ]
        })
        
        # Connect nodes in sequence
        mapping >> assessment >> gap_analysis >> checkpoint
        
        # Initialize with start node
        super().__init__(start=mapping)


class ExperienceDatabaseFlow(Flow):
    """
    Builds career database from document sources.
    
    This flow orchestrates the complete process of building a career database:
    1. Scans configured sources (Google Drive, local directories) for documents
    2. Extracts work experience using LLM analysis
    3. Builds structured career database with deduplication and validation
    
    The flow supports:
    - Checkpoint saving/loading for interrupted processing
    - Progress tracking throughout execution
    - Incremental updates to existing databases
    - Comprehensive error handling and reporting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the experience database flow.
        
        Args:
            config: Flow configuration including:
                - scan_config: Document source configuration
                - extraction_config: LLM extraction settings
                - output_path: Where to save career database
                - enable_checkpoints: Whether to save checkpoints
                - checkpoint_dir: Directory for checkpoint files
        """
        self.config = config or {}
        self.checkpoints_enabled = self.config.get("enable_checkpoints", True)
        self.checkpoint_dir = self.config.get("checkpoint_dir", ".checkpoints")
        self.start_time = None
        
        # Create nodes
        scan = ScanDocumentsNode()
        extract = ExtractExperienceNode()
        build = BuildDatabaseNode()
        
        # Add checkpoint nodes if enabled
        if self.checkpoints_enabled:
            # Create checkpoint nodes
            save_scan = SaveCheckpointNode()
            save_scan.set_params({
                "flow_name": "experience_db",
                "checkpoint_name": "scan_complete",
                "checkpoint_data": ["document_sources", "scan_errors"]
            })
            
            save_extract = SaveCheckpointNode()
            save_extract.set_params({
                "flow_name": "experience_db",
                "checkpoint_name": "extract_complete",
                "checkpoint_data": ["extracted_experiences", "extraction_summary"]
            })
            
            # Connect with checkpoints
            scan >> save_scan >> extract >> save_extract >> build
            
            # Initialize with start node
            super().__init__(start=scan)
        else:
            # Direct connection without checkpoints
            scan >> extract >> build
            super().__init__(start=scan)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the flow by setting up configuration and checking for resume.
        
        Args:
            shared: Shared store to populate with configuration
            
        Returns:
            Preparation context including resume status
        """
        import time
        from datetime import datetime
        from pathlib import Path
        
        self.start_time = time.time()
        
        # Apply configuration to shared store
        shared.update({
            "scan_config": self.config.get("scan_config", {
                "google_drive_folders": [],
                "local_directories": [],
                "file_types": [".pdf", ".docx", ".md"],
                "date_filter": {}
            }),
            "extraction_mode": self.config.get("extraction_config", {}).get("mode", "comprehensive"),
            "database_output_path": self.config.get("output_path", "career_database.yaml"),
            "merge_strategy": self.config.get("merge_strategy", "smart")
        })
        
        # Load existing database if requested
        if self.config.get("merge_with_existing", True):
            existing_db_path = Path(shared["database_output_path"])
            if existing_db_path.exists():
                try:
                    from utils.database_parser_v2 import load_career_database
                    shared["existing_career_database"] = load_career_database(existing_db_path)
                    logger.info(f"Loaded existing database from {existing_db_path}")
                except Exception as e:
                    logger.warning(f"Could not load existing database: {e}")
        
        # Check for checkpoint resume
        if self.checkpoints_enabled and self.config.get("resume_from_checkpoint", True):
            checkpoint_path = Path(self.checkpoint_dir) / "experience_db"
            if checkpoint_path.exists():
                latest_checkpoint = self._find_latest_checkpoint(checkpoint_path)
                if latest_checkpoint:
                    logger.info(f"Resuming from checkpoint: {latest_checkpoint}")
                    # LoadCheckpointNode will handle the actual loading
                    shared["resume_checkpoint"] = latest_checkpoint
        
        # Initialize progress tracking
        shared["flow_progress"] = {
            "scanning": {"status": "pending", "progress": 0},
            "extracting": {"status": "pending", "progress": 0},
            "building": {"status": "pending", "progress": 0}
        }
        
        return {"flow_initialized": True}
    
    def _find_latest_checkpoint(self, checkpoint_dir: Path) -> Optional[str]:
        """Find the most recent checkpoint in the directory."""
        checkpoints = list(checkpoint_dir.glob("*.yaml"))
        if not checkpoints:
            return None
        
        # Sort by modification time
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        return latest.stem  # Return checkpoint name without extension
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Any) -> str:
        """
        Generate final report and clean up.
        
        Args:
            shared: Shared store with all results
            prep_res: Preparation results
            exec_res: Execution results (final node action)
            
        Returns:
            Final action/status
        """
        import time
        
        # Calculate execution time
        duration = time.time() - self.start_time if self.start_time else 0
        
        # Generate comprehensive summary report
        summary = self._generate_summary_report(shared, duration)
        
        # Save summary to file
        if self.config.get("save_summary", True):
            self._save_summary(summary)
        
        # Log summary
        self._log_summary(summary)
        
        # Store summary in shared for caller
        shared["flow_summary"] = summary
        
        return "complete"
    
    def _generate_summary_report(self, shared: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """Generate comprehensive summary of the flow execution."""
        summary = {
            "flow_status": "completed",
            "duration_minutes": round(duration / 60, 1),
            "timestamp": datetime.now().isoformat()
        }
        
        # Scanning phase summary
        if "document_sources" in shared:
            docs = shared["document_sources"]
            summary["scanning_phase"] = {
                "documents_found": len(docs),
                "total_size_mb": round(sum(d.get("size", 0) for d in docs) / 1024 / 1024, 1),
                "sources": self._count_sources(docs),
                "errors": len(shared.get("scan_errors", []))
            }
        
        # Extraction phase summary
        if "extraction_summary" in shared:
            ext_summary = shared["extraction_summary"]
            summary["extraction_phase"] = {
                "documents_processed": ext_summary.get("total_documents", 0),
                "successful_extractions": ext_summary.get("successful_extractions", 0),
                "failed_extractions": ext_summary.get("failed_extractions", 0),
                "average_confidence": round(ext_summary.get("average_confidence", 0), 2)
            }
        
        # Building phase summary
        if "build_summary" in shared:
            build_summary = shared["build_summary"]
            summary["building_phase"] = {
                "experiences_before_dedup": build_summary.get("experiences_extracted", 0),
                "experiences_after_dedup": build_summary.get("experiences_after_dedup", 0),
                "companies": len(build_summary.get("companies", [])),
                "technologies_found": len(build_summary.get("technologies_found", [])),
                "validation_errors": len(build_summary.get("validation_errors", [])),
                "database_saved": shared.get("database_output_path")
            }
            
            # Add quality metrics
            if "extraction_quality" in build_summary:
                summary["quality_metrics"] = build_summary["extraction_quality"]
        
        # Add data completeness
        if "build_summary" in shared and "data_completeness" in shared["build_summary"]:
            summary["data_completeness"] = shared["build_summary"]["data_completeness"]
        
        # Add next steps
        summary["next_steps"] = self._generate_next_steps(summary)
        
        return summary
    
    def _count_sources(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count documents by source type."""
        sources = {}
        for doc in documents:
            source = doc.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def _generate_next_steps(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps based on summary."""
        next_steps = []
        
        # Check for extraction failures
        if summary.get("extraction_phase", {}).get("failed_extractions", 0) > 0:
            next_steps.append("Review and manually process failed document extractions")
        
        # Check for validation errors
        if summary.get("building_phase", {}).get("validation_errors", 0) > 0:
            next_steps.append("Fix validation errors in the generated database")
        
        # Check data completeness
        completeness = summary.get("data_completeness", {})
        if not completeness.get("has_email"):
            next_steps.append("Add email address to personal information")
        if not completeness.get("has_skills"):
            next_steps.append("Add technical skills section")
        
        # Always suggest review
        next_steps.append("Review extracted experiences for accuracy")
        next_steps.append("Add any missing experiences or projects manually")
        
        # Suggest next flow
        if summary.get("building_phase", {}).get("experiences_after_dedup", 0) > 0:
            next_steps.append("Run job application flows with the new career database")
        
        return next_steps
    
    def _save_summary(self, summary: Dict[str, Any]) -> None:
        """Save summary report to file."""
        from pathlib import Path
        import yaml
        
        summary_dir = Path("summaries")
        summary_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = summary_dir / f"experience_db_summary_{timestamp}.yaml"
        
        with open(summary_file, 'w') as f:
            yaml.dump(summary, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Summary saved to: {summary_file}")
    
    def _log_summary(self, summary: Dict[str, Any]) -> None:
        """Log summary to console."""
        logger.info("=" * 60)
        logger.info("EXPERIENCE DATABASE FLOW COMPLETE")
        logger.info("=" * 60)
        
        logger.info(f"Duration: {summary['duration_minutes']} minutes")
        
        if "scanning_phase" in summary:
            scan = summary["scanning_phase"]
            logger.info(f"\nScanning Phase:")
            logger.info(f"  - Documents found: {scan['documents_found']}")
            logger.info(f"  - Total size: {scan['total_size_mb']} MB")
            logger.info(f"  - Sources: {scan['sources']}")
        
        if "extraction_phase" in summary:
            extract = summary["extraction_phase"]
            logger.info(f"\nExtraction Phase:")
            logger.info(f"  - Processed: {extract['documents_processed']}")
            logger.info(f"  - Successful: {extract['successful_extractions']}")
            logger.info(f"  - Failed: {extract['failed_extractions']}")
            logger.info(f"  - Avg confidence: {extract['average_confidence']}")
        
        if "building_phase" in summary:
            build = summary["building_phase"]
            logger.info(f"\nBuilding Phase:")
            logger.info(f"  - Experiences (raw): {build['experiences_before_dedup']}")
            logger.info(f"  - Experiences (final): {build['experiences_after_dedup']}")
            logger.info(f"  - Companies: {build['companies']}")
            logger.info(f"  - Technologies: {build['technologies_found']}")
            logger.info(f"  - Database: {build['database_saved']}")
        
        if summary.get("next_steps"):
            logger.info(f"\nNext Steps:")
            for step in summary["next_steps"]:
                logger.info(f"  - {step}")
        
        logger.info("=" * 60)


class NarrativeFlow(Flow):
    """
    Develops narrative strategy for the application.
    
    This flow chains ExperiencePrioritizationNode and NarrativeStrategyNode
    to create a complete narrative strategy, then saves a checkpoint for
    user review and editing before document generation.
    """
    
    def __init__(self):
        # Create nodes
        prioritize = ExperiencePrioritizationNode()
        strategy = NarrativeStrategyNode()
        checkpoint = SaveCheckpointNode()
        
        # Configure checkpoint to save narrative elements
        checkpoint.set_params({
            "flow_name": "narrative",
            "checkpoint_data": [
                "prioritized_experiences",
                "narrative_strategy",
                "suitability_assessment",
                "requirements",
                "job_title",
                "company_name"
            ],
            "output_file": "narrative_output.yaml",
            "user_message": """
Narrative strategy has been saved to narrative_output.yaml

You can now review and edit:
- Must-tell experiences and their key points
- Career arc (past, present, future)
- Key messages to emphasize
- Evidence stories (CAR format)
- Differentiators that set you apart

Once you're satisfied with the narrative, run the generation flow
to create your tailored CV and cover letter.
"""
        })
        
        # Connect nodes in sequence
        prioritize >> strategy >> checkpoint
        
        # Initialize with start node
        super().__init__(start=prioritize)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required inputs for narrative flow."""
        required_fields = [
            "career_db",
            "requirements", 
            "suitability_assessment",
            "job_title",
            "company_name"
        ]
        
        missing_fields = [field for field in required_fields if field not in shared]
        
        if missing_fields:
            logger.warning(f"NarrativeFlow missing required fields: {missing_fields}")
            # Initialize missing fields with sensible defaults
            if "career_db" not in shared:
                raise ValueError("Career database is required for narrative flow")
            if "requirements" not in shared:
                shared["requirements"] = {}
            if "suitability_assessment" not in shared:
                logger.warning("Running narrative flow without suitability assessment")
                shared["suitability_assessment"] = {
                    "technical_fit_score": 70,
                    "cultural_fit_score": 70,
                    "key_strengths": ["Strong technical background"],
                    "unique_value_proposition": "Experienced professional"
                }
            if "job_title" not in shared:
                shared["job_title"] = "Position"
            if "company_name" not in shared:
                shared["company_name"] = "Company"
        
        # Set current date if not present
        if "current_date" not in shared:
            from datetime import datetime
            shared["current_date"] = datetime.now().strftime("%Y-%m-%d")
        
        return {"input_validation": "complete"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Any) -> Dict[str, Any]:
        """Log completion and provide next steps."""
        logger.info("=" * 50)
        logger.info("NARRATIVE FLOW COMPLETE")
        logger.info("=" * 50)
        
        if "prioritized_experiences" in shared:
            logger.info(f"Prioritized {len(shared['prioritized_experiences'])} experiences")
        
        if "narrative_strategy" in shared:
            strategy = shared["narrative_strategy"]
            logger.info(f"Generated narrative with:")
            logger.info(f"  - {len(strategy.get('must_tell_experiences', []))} must-tell experiences")
            logger.info(f"  - {len(strategy.get('differentiators', []))} differentiators")
            logger.info(f"  - {len(strategy.get('key_messages', []))} key messages")
            logger.info(f"  - {len(strategy.get('evidence_stories', []))} evidence stories")
        
        logger.info("=" * 50)
        
        return shared


class GenerationFlow(BatchFlow):
    """
    Generates final application documents.
    
    Creates tailored CV and cover letter based on narrative strategy.
    This flow uses BatchFlow to run both generation nodes in parallel
    for efficiency, since they have independent outputs.
    """
    
    def __init__(self):
        # Start by loading checkpoint from narrative flow
        load = LoadCheckpointNode()
        load.set_params({"flow_name": "narrative"})
        
        # Create generation nodes
        cv_gen = CVGenerationNode()
        cover_letter_gen = CoverLetterNode()
        
        # Connect load node to both generation nodes (parallel execution)
        load >> cv_gen
        load >> cover_letter_gen
        
        super().__init__(start=load)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all required inputs are present for generation."""
        required_fields = [
            "narrative_strategy",
            "career_db",
            "requirements",
            "job_title", 
            "company_name"
        ]
        
        missing_fields = [field for field in required_fields if field not in shared]
        
        if missing_fields:
            logger.warning(f"GenerationFlow missing fields: {missing_fields}")
            
            # Critical fields that must exist
            if "narrative_strategy" not in shared:
                raise ValueError("Cannot generate materials without narrative strategy")
            if "career_db" not in shared:
                raise ValueError("Cannot generate materials without career database")
        
        # Optional but recommended
        if "company_research" not in shared:
            logger.warning("No company research available - cover letter will be generic")
        
        if "suitability_assessment" not in shared:
            logger.warning("No suitability assessment - using defaults")
            shared["suitability_assessment"] = {
                "technical_fit_score": 75,
                "cultural_fit_score": 75,
                "key_strengths": ["Technical expertise"],
                "unique_value_proposition": "Strong technical background"
            }
        
        return {"input_validation": "complete"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Any) -> Dict[str, Any]:
        """Validate outputs and log generation summary."""
        # Check outputs were generated
        cv_generated = "cv_markdown" in shared and shared["cv_markdown"]
        letter_generated = "cover_letter_text" in shared and shared["cover_letter_text"]
        
        logger.info("=" * 50)
        logger.info("GENERATION FLOW COMPLETE")
        logger.info("=" * 50)
        
        if cv_generated:
            cv_lines = shared["cv_markdown"].split('\n')
            logger.info(f"✓ CV generated: {len(cv_lines)} lines")
        else:
            logger.error("✗ CV generation failed")
        
        if letter_generated:
            letter_words = len(shared["cover_letter_text"].split())
            logger.info(f"✓ Cover letter generated: {letter_words} words")
        else:
            logger.error("✗ Cover letter generation failed")
        
        # Save final outputs to files
        if cv_generated and letter_generated:
            self._save_outputs(shared)
            logger.info("✓ Materials saved to outputs directory")
        
        logger.info("=" * 50)
        
        return shared
    
    def _save_outputs(self, shared: Dict[str, Any]) -> None:
        """Save generated materials to output files."""
        from pathlib import Path
        import datetime
        
        # Create outputs directory
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title = shared.get("job_title", "position").replace(" ", "_")
        company = shared.get("company_name", "company").replace(" ", "_")
        
        # Save CV
        cv_filename = f"{timestamp}_{company}_{job_title}_CV.md"
        cv_path = output_dir / cv_filename
        with open(cv_path, 'w') as f:
            f.write(shared["cv_markdown"])
        
        # Save cover letter
        letter_filename = f"{timestamp}_{company}_{job_title}_CoverLetter.txt"
        letter_path = output_dir / letter_filename
        with open(letter_path, 'w') as f:
            f.write(shared["cover_letter_text"])
        
        logger.info(f"  - CV: {cv_filename}")
        logger.info(f"  - Cover Letter: {letter_filename}")


class CompanyResearchAgent(Flow):
    """
    Autonomous agent that researches a company for job applications.
    
    This flow implements a looping agent architecture where DecideActionNode
    acts as the cognitive core, directing research activities through tool nodes.
    The agent continues until it has gathered sufficient information about:
    - Company mission and values
    - Team scope and structure
    - Strategic importance of the role
    - Company culture and work environment
    
    The flow includes safety limits to prevent infinite loops.
    """
    
    def __init__(self, max_iterations: int = 20):
        """
        Initialize the research agent flow.
        
        Args:
            max_iterations: Maximum number of decision loops before forcing termination
        """
        self.max_iterations = max_iterations
        self.iteration_count = 0
        
        # Create all nodes
        decide = DecideActionNode()
        web_search = WebSearchNode()
        read_content = ReadContentNode()
        synthesize = SynthesizeInfoNode()
        
        # Create the agent loop structure
        # DecideActionNode is the hub that routes to tool nodes
        decide - "web_search" >> web_search
        decide - "read_content" >> read_content
        decide - "synthesize" >> synthesize
        
        # All tool nodes return to decide node
        web_search - "decide" >> decide
        read_content - "decide" >> decide
        synthesize - "decide" >> decide
        
        # The 'finish' action exits the flow
        # No explicit connection needed - Flow handles terminal actions
        
        # Initialize with decide node as entry point
        super().__init__(start=decide)
        
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the research agent by initializing research template.
        
        Args:
            shared: Shared store containing company_name and optional job_title
            
        Returns:
            Preparation context
        """
        # Initialize research template if not present
        if "company_research" not in shared:
            shared["company_research"] = {
                "mission": None,
                "team_scope": None,
                "strategic_importance": None,
                "culture": None,
                "technology_stack_practices": None,
                "recent_developments": None,
                "market_position_growth": None
            }
        
        # Reset iteration counter
        self.iteration_count = 0
        
        return {"max_iterations": self.max_iterations}
    
    def get_next_node(self, curr, action):
        """
        Override to implement iteration limiting and loop prevention.
        
        Args:
            curr: Current node
            action: Action returned by current node
            
        Returns:
            Next node or None to terminate
        """
        # Increment iteration counter
        self.iteration_count += 1
        
        # Check iteration limit
        if self.iteration_count >= self.max_iterations:
            logger.warning(f"Research agent hit maximum iteration limit ({self.max_iterations})")
            return None
        
        # Check for finish action
        if action == "finish":
            logger.info(f"Research completed after {self.iteration_count} iterations")
            return None
        
        # Use parent class logic for routing
        return super().get_next_node(curr, action)


class AssessmentFlow(Flow):
    """
    Evaluates candidate suitability using comprehensive scoring.
    
    This flow takes the outputs from AnalysisFlow (requirement mappings and gaps)
    and CompanyResearchAgent (company insights) to produce a quantitative and
    qualitative assessment that guides narrative strategy and material generation.
    
    The assessment includes:
    - Technical fit score (0-100)
    - Cultural fit score (0-100)
    - Key strengths identification
    - Critical gaps analysis
    - Unique value proposition
    - Overall hiring recommendation
    """
    
    def __init__(self):
        """Initialize the assessment flow with SuitabilityScoringNode."""
        # Create the scoring node
        scoring = SuitabilityScoringNode()
        
        # Simple linear flow: start -> scoring -> end
        super().__init__(start=scoring)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate required inputs are available.
        
        Required inputs:
        - requirement_mapping_final: From AnalysisFlow
        - gaps: From AnalysisFlow
        - company_research: From CompanyResearchAgent
        - requirements: Original job requirements
        - job_title: Position title
        - company_name: Company name
        """
        required_fields = [
            "requirement_mapping_final",
            "gaps",
            "requirements",
            "job_title",
            "company_name"
        ]
        
        missing_fields = [field for field in required_fields if field not in shared]
        
        if missing_fields:
            logger.warning(f"AssessmentFlow missing required fields: {missing_fields}")
            # Initialize missing fields with defaults
            for field in missing_fields:
                if field == "requirement_mapping_final":
                    shared[field] = {}
                elif field == "gaps":
                    shared[field] = []
                elif field == "requirements":
                    shared[field] = {}
                elif field in ["job_title", "company_name"]:
                    shared[field] = "Unknown"
        
        # Company research is optional but recommended
        if "company_research" not in shared:
            logger.warning("No company research available for cultural fit assessment")
            shared["company_research"] = {}
        
        return {"input_validation": "complete"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Any) -> Dict[str, Any]:
        """
        Validate assessment output and log summary.
        
        The SuitabilityScoringNode should have populated:
        - shared["suitability_assessment"]: Complete assessment results
        """
        if "suitability_assessment" not in shared:
            logger.error("AssessmentFlow failed to produce suitability assessment")
            return shared
        
        assessment = shared["suitability_assessment"]
        
        # Log assessment summary
        logger.info("=" * 50)
        logger.info("SUITABILITY ASSESSMENT COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Technical Fit Score: {assessment.get('technical_fit_score', 'N/A')}/100")
        logger.info(f"Cultural Fit Score: {assessment.get('cultural_fit_score', 'N/A')}/100")
        logger.info(f"Key Strengths: {len(assessment.get('key_strengths', []))}")
        logger.info(f"Critical Gaps: {len(assessment.get('critical_gaps', []))}")
        
        if assessment.get('overall_recommendation'):
            logger.info(f"\nRecommendation: {assessment['overall_recommendation'][:100]}...")
        
        logger.info("=" * 50)
        
        return shared


# Utility function to create complete application workflow
def create_application_workflow() -> Flow:
    """
    Creates the complete job application workflow.
    
    This connects all major flows in sequence with appropriate
    checkpoint handling.
    """
    # For now, return a simple flow
    # In future, this would connect all flows
    return RequirementExtractionFlow()