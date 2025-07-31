"""
PocketFlow flow orchestration for career application agent.

This module implements the flow logic that connects nodes in a directed graph.
It manages the execution order and data flow between nodes.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import asyncio
from nodes import Node


@dataclass
class Edge:
    """Represents an edge in the flow graph."""
    source: str
    target: str
    condition: Optional[callable] = None


@dataclass
class Flow:
    """
    Represents a directed graph of nodes.
    
    Manages node execution order and shared store data flow.
    """
    name: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    store: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: Node) -> 'Flow':
        """Add a node to the flow."""
        self.nodes[node.name] = node
        return self
    
    def add_edge(self, source: str, target: str, condition: Optional[callable] = None) -> 'Flow':
        """Add an edge between nodes."""
        self.edges.append(Edge(source, target, condition))
        return self
    
    def get_dependencies(self, node_name: str) -> Set[str]:
        """Get all nodes that must execute before the given node."""
        dependencies = set()
        for edge in self.edges:
            if edge.target == node_name:
                dependencies.add(edge.source)
        return dependencies
    
    def get_next_nodes(self, node_name: str) -> List[str]:
        """Get nodes that can execute after the given node."""
        next_nodes = []
        for edge in self.edges:
            if edge.source == node_name:
                if edge.condition is None or edge.condition(self.store):
                    next_nodes.append(edge.target)
        return next_nodes
    
    async def execute(self, start_node: Optional[str] = None) -> Dict[str, Any]:
        """Execute the flow starting from a specific node or entry points."""
        executed = set()
        
        # Find entry points (nodes with no dependencies) if no start node specified
        if start_node is None:
            entry_points = []
            for node_name in self.nodes:
                if not self.get_dependencies(node_name):
                    entry_points.append(node_name)
        else:
            entry_points = [start_node]
        
        # Execute nodes in topological order
        async def execute_node(node_name: str):
            if node_name in executed:
                return
            
            # Wait for dependencies
            dependencies = self.get_dependencies(node_name)
            for dep in dependencies:
                if dep not in executed:
                    await execute_node(dep)
            
            # Execute the node
            node = self.nodes[node_name]
            result = await node.execute(self.store)
            self.store.update(result)
            executed.add(node_name)
            
            # Execute next nodes
            next_nodes = self.get_next_nodes(node_name)
            await asyncio.gather(*[execute_node(next_node) for next_node in next_nodes])
        
        # Execute from all entry points
        await asyncio.gather(*[execute_node(entry) for entry in entry_points])
        
        return self.store


# Placeholder flows - will be implemented in subsequent tasks
class RequirementExtractionFlow(Flow):
    """Flow for extracting and analyzing job requirements."""
    pass


class AnalysisFlow(Flow):
    """Flow for analyzing candidate fit."""
    pass


class CompanyResearchFlow(Flow):
    """Flow for researching company information."""
    pass


class AssessmentFlow(Flow):
    """Flow for assessing overall suitability."""
    pass


class NarrativeFlow(Flow):
    """Flow for developing application narrative."""
    pass


class GenerationFlow(Flow):
    """Flow for generating application documents."""
    pass