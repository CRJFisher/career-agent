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
    SuitabilityScoringNode
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
    
    Prioritizes experiences and creates a cohesive story,
    with checkpoint for user review.
    """
    
    def __init__(self):
        # TODO: Add ExperiencePrioritizationNode
        # TODO: Add NarrativeStrategyNode
        checkpoint = SaveCheckpointNode()
        checkpoint.set_params({"flow_name": "narrative"})
        
        # For now, just checkpoint
        super().__init__(start=checkpoint)


class GenerationFlow(Flow):
    """
    Generates final application documents.
    
    Creates tailored CV and cover letter based on narrative strategy.
    """
    
    def __init__(self):
        # Start by loading checkpoint from narrative flow
        load = LoadCheckpointNode()
        load.set_params({"flow_name": "narrative"})
        
        # TODO: Add CVGenerationNode
        # TODO: Add CoverLetterNode
        
        super().__init__(start=load)


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