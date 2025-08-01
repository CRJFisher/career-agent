#!/usr/bin/env python3
"""
Simple demonstration of PocketFlow patterns in the career application agent.

This example shows:
1. How nodes implement the 3-step pattern (prep, exec, post)
2. How flows connect nodes with action-based transitions
3. How the shared store enables communication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pocketflow import Node, Flow
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')
logger = logging.getLogger(__name__)


class GreetingNode(Node):
    """Simple node that generates a greeting."""
    
    def prep(self, shared):
        """Read name from shared store."""
        name = shared.get('name', 'World')
        logger.info(f"GreetingNode prep: Got name '{name}'")
        return name
    
    def exec(self, name):
        """Generate greeting message."""
        greeting = f"Hello, {name}!"
        logger.info(f"GreetingNode exec: Generated '{greeting}'")
        return greeting
    
    def post(self, shared, prep_res, exec_res):
        """Store greeting in shared store."""
        shared['greeting'] = exec_res
        logger.info(f"GreetingNode post: Stored greeting")
        
        # Decide next action based on whether name was provided
        if prep_res == 'World':
            return "generic"
        else:
            return "personalized"


class GenericFollowupNode(Node):
    """Node for generic follow-up."""
    
    def exec(self, prep_res):
        message = "Please tell me your name for a personalized experience."
        logger.info(f"GenericFollowupNode: {message}")
        return message
    
    def post(self, shared, prep_res, exec_res):
        shared['followup'] = exec_res
        return "default"


class PersonalizedFollowupNode(Node):
    """Node for personalized follow-up."""
    
    def prep(self, shared):
        return shared.get('name', 'Friend')
    
    def exec(self, name):
        message = f"Nice to meet you, {name}! How can I help you today?"
        logger.info(f"PersonalizedFollowupNode: {message}")
        return message
    
    def post(self, shared, prep_res, exec_res):
        shared['followup'] = exec_res
        return "default"


class FinalNode(Node):
    """Final node that summarizes the interaction."""
    
    def prep(self, shared):
        return {
            'greeting': shared.get('greeting', ''),
            'followup': shared.get('followup', '')
        }
    
    def exec(self, data):
        summary = f"Summary: {data['greeting']} - {data['followup']}"
        logger.info(f"FinalNode: {summary}")
        return summary
    
    def post(self, shared, prep_res, exec_res):
        shared['summary'] = exec_res
        return None  # End of flow


def demo_action_based_flow():
    """Demonstrate action-based flow transitions."""
    print("=== Action-Based Flow Demo ===")
    
    # Create nodes
    greeting = GreetingNode()
    generic = GenericFollowupNode()
    personalized = PersonalizedFollowupNode()
    final = FinalNode()
    
    # Define transitions using action strings
    greeting - "generic" >> generic
    greeting - "personalized" >> personalized
    generic >> final
    personalized >> final
    
    # Create the flow starting with greeting
    flow = Flow(start=greeting)
    
    # Test with no name (generic path)
    print("\n--- Test 1: No name provided ---")
    shared1 = {}
    flow.run(shared1)
    print(f"Result: {shared1.get('summary', 'No summary')}")
    
    # Test with name (personalized path)
    print("\n--- Test 2: Name provided ---")
    shared2 = {'name': 'Alice'}
    flow.run(shared2)
    print(f"Result: {shared2.get('summary', 'No summary')}")


def demo_sequential_flow():
    """Demonstrate sequential flow."""
    print("\n\n=== Sequential Flow Demo ===")
    
    class StepNode(Node):
        def __init__(self, step_num):
            super().__init__()
            self.step_num = step_num
            
        def exec(self, prep_res):
            message = f"Executing step {self.step_num}"
            logger.info(message)
            return message
        
        def post(self, shared, prep_res, exec_res):
            if 'steps' not in shared:
                shared['steps'] = []
            shared['steps'].append(exec_res)
            return "default"
    
    # Create nodes
    steps = [StepNode(i) for i in range(1, 4)]
    
    # Connect nodes sequentially
    for i in range(len(steps) - 1):
        steps[i] >> steps[i + 1]
    
    # Create flow
    flow = Flow(start=steps[0])
    
    # Run flow
    shared = {}
    flow.run(shared)
    
    print("Completed steps:")
    for step in shared['steps']:
        print(f"  - {step}")


def demo_nested_flow():
    """Demonstrate nested flows."""
    print("\n\n=== Nested Flow Demo ===")
    
    # Create a sub-flow
    step1 = GreetingNode()
    step2 = PersonalizedFollowupNode()
    step1 >> step2
    
    subflow = Flow(start=step1)
    
    # Create main flow with subflow as a node
    start = GenericFollowupNode()
    final = FinalNode()
    start >> subflow >> final
    
    main_flow = Flow(start=start)
    
    # Run the flow
    shared = {'name': 'Bob'}
    main_flow.run(shared)
    
    print(f"\nFinal summary: {shared.get('summary', 'No summary generated')}")


if __name__ == "__main__":
    demo_action_based_flow()
    demo_sequential_flow()
    demo_nested_flow()