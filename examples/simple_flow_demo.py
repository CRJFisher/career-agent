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

from nodes import Node
from flow import Flow, create_flow
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
    
    def exec(self, prep_res):
        """Generate greeting message."""
        greeting = f"Hello, {prep_res}!"
        logger.info(f"GreetingNode exec: Generated '{greeting}'")
        return greeting
    
    def post(self, shared, prep_res, exec_res):
        """Store greeting and decide next action."""
        shared['greeting'] = exec_res
        logger.info(f"GreetingNode post: Stored greeting")
        
        # Return different actions based on name
        if prep_res.lower() == "world":
            return "generic"
        else:
            return "personalized"


class GenericFollowupNode(Node):
    """Node for generic follow-up."""
    
    def exec(self, prep_res):
        return "Welcome to PocketFlow! Please provide your name for a personalized experience."
    
    def post(self, shared, prep_res, exec_res):
        shared['followup'] = exec_res
        logger.info("GenericFollowupNode: Added generic message")
        return "default"


class PersonalizedFollowupNode(Node):
    """Node for personalized follow-up."""
    
    def prep(self, shared):
        return shared.get('name', 'Friend')
    
    def exec(self, prep_res):
        return f"Great to meet you, {prep_res}! Let's process your job application."
    
    def post(self, shared, prep_res, exec_res):
        shared['followup'] = exec_res
        logger.info("PersonalizedFollowupNode: Added personalized message")
        return "default"


class FinalNode(Node):
    """Final node that summarizes the interaction."""
    
    def prep(self, shared):
        return {
            'greeting': shared.get('greeting'),
            'followup': shared.get('followup')
        }
    
    def exec(self, prep_res):
        summary = f"Conversation summary:\n1. {prep_res['greeting']}\n2. {prep_res['followup']}"
        return summary
    
    def post(self, shared, prep_res, exec_res):
        shared['summary'] = exec_res
        logger.info("FinalNode: Created summary")
        return "complete"


def demo_basic_flow():
    """Demonstrate basic flow with conditional transitions."""
    print("\n=== Basic Flow Demo ===")
    
    # Create nodes
    greeting = GreetingNode(name="Greeting")
    generic = GenericFollowupNode(name="GenericFollowup")
    personal = PersonalizedFollowupNode(name="PersonalizedFollowup")
    final = FinalNode(name="Final")
    
    # Connect nodes with action-based transitions
    greeting - "generic" >> generic
    greeting - "personalized" >> personal
    generic >> final
    personal >> final
    
    # Create flow
    flow = Flow(start=greeting, name="GreetingFlow")
    
    # Test with generic name
    print("\nTest 1: Generic greeting")
    shared = {'name': 'World'}
    flow.run(shared)
    print(f"Result: {shared['summary']}")
    
    # Test with personalized name
    print("\nTest 2: Personalized greeting")
    shared = {'name': 'Alice'}
    flow.run(shared)
    print(f"Result: {shared['summary']}")


def demo_sequential_flow():
    """Demonstrate sequential flow creation helper."""
    print("\n\n=== Sequential Flow Demo ===")
    
    # Create simple sequential nodes
    class StepNode(Node):
        def __init__(self, step_num):
            super().__init__(name=f"Step{step_num}")
            self.step_num = step_num
        
        def exec(self, prep_res):
            return f"Completed step {self.step_num}"
        
        def post(self, shared, prep_res, exec_res):
            if 'steps' not in shared:
                shared['steps'] = []
            shared['steps'].append(exec_res)
            return "default"
    
    # Create nodes
    steps = [StepNode(i) for i in range(1, 4)]
    
    # Create flow using helper
    flow = create_flow("SequentialFlow", *steps)
    
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
    step1 = GreetingNode(name="SubGreeting")
    step2 = PersonalizedFollowupNode(name="SubFollowup")
    step1 >> step2
    
    subflow = Flow(start=step1, name="SubFlow")
    
    # Create main flow with subflow as a node
    start = GenericFollowupNode(name="MainStart")
    start >> subflow >> FinalNode(name="MainFinal")
    
    main_flow = Flow(start=start, name="MainFlow")
    
    # Visualize the flow
    print("\nFlow structure:")
    print(main_flow.visualize())
    
    # Run the flow
    shared = {'name': 'Bob'}
    main_flow.run(shared)
    
    print(f"\nFinal summary: {shared.get('summary', 'No summary generated')}")


if __name__ == "__main__":
    # Run all demos
    demo_basic_flow()
    demo_sequential_flow()
    demo_nested_flow()
    
    print("\n✅ All demos completed successfully!")