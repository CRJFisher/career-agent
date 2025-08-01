"""
Career application agent flows.

This module implements the application-specific flows that orchestrate nodes
for the career application system. Each flow represents a complete workflow
or pipeline in the job application process.

All flows extend PocketFlow's base Flow class.
"""

from typing import Optional
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
    ExtractExperienceNode
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