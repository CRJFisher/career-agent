"""
Career application agent flows.

This module implements the application-specific flows that orchestrate nodes
for the career application system. Each flow represents a complete workflow
or pipeline in the job application process.

All flows extend PocketFlow's base Flow class.
"""

from typing import Optional, Dict, Any
import logging
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
    
    Scans Google Drive and local directories, extracts work experience,
    and builds a structured career database.
    """
    
    def __init__(self):
        # Create nodes
        scan = ScanDocumentsNode()
        extract = ExtractExperienceNode()
        # TODO: Add BuildDatabaseNode
        
        # Connect nodes
        scan >> extract
        
        # Initialize with start node
        super().__init__(start=scan)


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