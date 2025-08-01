"""
PocketFlow flow orchestration for career application agent.

This module implements the flow logic that connects nodes in a directed graph.
Following PocketFlow patterns, flows are created by connecting nodes with
action-based transitions using >> and - operators.
"""

from typing import Dict, Any, Optional, Set, List
import logging
from nodes import Node

logger = logging.getLogger(__name__)


class Flow(Node):
    """
    A Flow is a special type of Node that orchestrates other nodes.
    
    In PocketFlow, a Flow:
    - Acts as a container for connected nodes
    - Executes from a start node following action-based transitions
    - Can be nested within other flows
    """
    
    def __init__(self, start: Node, name: str = None):
        """
        Initialize a flow.
        
        Args:
            start: The entry point node
            name: Flow name (defaults to class name)
        """
        super().__init__(name=name or self.__class__.__name__)
        self.start = start
        self._executed_nodes = set()
    
    def prep(self, shared: Dict[str, Any]) -> Any:
        """Flows typically don't need prep."""
        return None
    
    def exec(self, prep_res: Any) -> Any:
        """Flows don't execute logic directly - they orchestrate nodes."""
        # This won't be called since run() overrides the execution
        return None
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any) -> Optional[str]:
        """Flows can return an action based on their execution results."""
        # Check if flow completed successfully
        if shared.get('flow_error'):
            return "error"
        return "default"
    
    def run(self, shared: Dict[str, Any]) -> Optional[str]:
        """
        Run the flow by executing nodes following transitions.
        
        Args:
            shared: The shared data store
            
        Returns:
            Final action from the flow
        """
        self._executed_nodes.clear()
        
        try:
            # Start execution from the start node
            current_node = self.start
            
            while current_node is not None:
                # Skip if already executed (prevent infinite loops)
                if current_node.name in self._executed_nodes:
                    logger.warning(f"Node {current_node.name} already executed, stopping to prevent loop")
                    break
                
                # Execute the current node
                logger.info(f"Executing node: {current_node.name}")
                action = current_node.run(shared)
                self._executed_nodes.add(current_node.name)
                
                # Find next node based on action
                if hasattr(current_node, '_transitions') and action in current_node._transitions:
                    current_node = current_node._transitions[action]
                    logger.info(f"Transitioning with action '{action}' to node: {current_node.name}")
                else:
                    # No transition for this action, flow ends
                    logger.info(f"Flow ending - no transition defined for action '{action}'")
                    current_node = None
            
            # Flow completed successfully
            shared['flow_status'] = 'completed'
            shared['flow_error'] = None
            
        except Exception as e:
            logger.error(f"Flow execution error: {e}")
            shared['flow_status'] = 'error'
            shared['flow_error'] = str(e)
            raise
        
        # Call post to determine final action
        return self.post(shared, None, None)
    
    def visualize(self) -> str:
        """
        Generate a simple text visualization of the flow.
        
        Returns:
            String representation of the flow structure
        """
        visited = set()
        lines = [f"Flow: {self.name}"]
        lines.append("=" * (len(lines[0]) + 5))
        
        def traverse(node: Node, indent: int = 0):
            if node.name in visited:
                return
            visited.add(node.name)
            
            prefix = "  " * indent + "→ " if indent > 0 else ""
            lines.append(f"{prefix}{node.name}")
            
            if hasattr(node, '_transitions'):
                for action, next_node in node._transitions.items():
                    lines.append(f"  {'  ' * indent}  [{action}]")
                    traverse(next_node, indent + 1)
        
        traverse(self.start)
        return "\n".join(lines)


class RequirementExtractionFlow(Flow):
    """Flow for extracting and analyzing job requirements."""
    
    def __init__(self):
        # Import here to avoid circular imports
        from nodes import ExtractRequirementsNode
        
        # Create nodes
        extract_node = ExtractRequirementsNode()
        
        # No transitions needed for single-node flow
        # The flow will execute the node and complete
        
        super().__init__(start=extract_node, name="RequirementExtractionFlow")
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any) -> Optional[str]:
        """Determine flow result based on extraction status."""
        if shared.get('extraction_status') == 'success':
            return "success"
        else:
            return "failed"


class AnalysisFlow(Flow):
    """Flow for analyzing candidate fit."""
    
    def __init__(self):
        # Import nodes
        from nodes import RequirementMappingNode, StrengthAssessmentNode, GapAnalysisNode
        
        # Create nodes
        mapping = RequirementMappingNode()
        strengths = StrengthAssessmentNode()
        gaps = GapAnalysisNode()
        
        # Connect nodes
        mapping >> strengths >> gaps
        
        super().__init__(start=mapping, name="AnalysisFlow")


class CompanyResearchFlow(Flow):
    """Flow for researching company information."""
    
    def __init__(self):
        # Import nodes
        from nodes import DecideActionNode, CompanyResearchNode
        
        # Create nodes
        decide = DecideActionNode()
        research = CompanyResearchNode()
        
        # Connect with conditional transition
        decide - "research" >> research
        # If no research needed, flow ends after decide
        
        super().__init__(start=decide, name="CompanyResearchFlow")


class AssessmentFlow(Flow):
    """Flow for assessing overall suitability."""
    
    def __init__(self):
        # Import nodes
        from nodes import SuitabilityScoringNode
        
        # Single node flow
        scoring = SuitabilityScoringNode()
        
        super().__init__(start=scoring, name="AssessmentFlow")


class NarrativeFlow(Flow):
    """Flow for developing application narrative."""
    
    def __init__(self):
        # Import nodes
        from nodes import ExperiencePrioritizationNode, NarrativeStrategyNode
        
        # Create nodes
        prioritize = ExperiencePrioritizationNode()
        narrative = NarrativeStrategyNode()
        
        # Connect nodes
        prioritize >> narrative
        
        super().__init__(start=prioritize, name="NarrativeFlow")


class GenerationFlow(Flow):
    """Flow for generating application documents."""
    
    def __init__(self):
        # Import nodes
        from nodes import CVGenerationNode, CoverLetterNode
        
        # Create nodes
        cv = CVGenerationNode()
        cover = CoverLetterNode()
        
        # Generate both documents
        cv >> cover
        
        super().__init__(start=cv, name="GenerationFlow")


# Convenience function for creating flows
def create_flow(name: str, *nodes: Node) -> Flow:
    """
    Create a flow from a sequence of nodes.
    
    Args:
        name: Flow name
        *nodes: Nodes to connect in sequence
        
    Returns:
        Flow starting from the first node
    """
    if not nodes:
        raise ValueError("At least one node required")
    
    # Connect nodes in sequence
    for i in range(len(nodes) - 1):
        nodes[i] >> nodes[i + 1]
    
    # Create flow with custom name
    flow = Flow(start=nodes[0], name=name)
    return flow