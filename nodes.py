"""
PocketFlow nodes for career application agent.

This module implements the nodes for the career application orchestration system.
Each node represents a discrete unit of work in the job application process.

Following PocketFlow patterns, each node implements:
- prep(shared): Read and preprocess data from shared store
- exec(prep_res): Execute compute logic (mainly LLM calls)
- post(shared, prep_res, exec_res): Write results and return action
"""

from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import time
import logging

logger = logging.getLogger(__name__)


class Node(ABC):
    """
    Base class for all nodes in the PocketFlow framework.
    
    Implements the 3-step execution pattern:
    1. prep - Read from shared store
    2. exec - Execute computation
    3. post - Write to shared store and return action
    """
    
    def __init__(self, name: str = None, max_retries: int = 1, wait: int = 0):
        """
        Initialize a node.
        
        Args:
            name: Node name (defaults to class name)
            max_retries: Maximum execution attempts (default 1 = no retry)
            wait: Seconds to wait between retries (default 0)
        """
        self.name = name or self.__class__.__name__
        self.max_retries = max_retries
        self.wait = wait
        self.cur_retry = 0
        self.params = {}
        self._transitions = {}  # action -> node mapping
    
    def prep(self, shared: Dict[str, Any]) -> Any:
        """
        Read and preprocess data from shared store.
        
        Args:
            shared: The shared data store
            
        Returns:
            Preprocessed data for exec()
        """
        return None
    
    @abstractmethod
    def exec(self, prep_res: Any) -> Any:
        """
        Execute compute logic.
        
        Args:
            prep_res: Result from prep()
            
        Returns:
            Execution result for post()
        """
        pass
    
    def exec_fallback(self, prep_res: Any, exc: Exception) -> Any:
        """
        Handle execution failure after all retries.
        
        Args:
            prep_res: Result from prep()
            exc: The exception that caused failure
            
        Returns:
            Fallback result for post()
        """
        raise exc
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any) -> Optional[str]:
        """
        Postprocess and write data to shared store.
        
        Args:
            shared: The shared data store
            prep_res: Result from prep()
            exec_res: Result from exec()
            
        Returns:
            Action string for flow transition (None = "default")
        """
        return None
    
    def set_params(self, params: Dict[str, Any]) -> 'Node':
        """Set node parameters."""
        self.params = params
        return self
    
    def run(self, shared: Dict[str, Any]) -> Optional[str]:
        """
        Run the node's 3-step execution.
        
        Args:
            shared: The shared data store
            
        Returns:
            Action string from post()
        """
        # Step 1: Prep
        prep_res = self.prep(shared)
        
        # Step 2: Exec with retries
        exec_res = None
        self.cur_retry = 0
        
        while self.cur_retry < self.max_retries:
            try:
                exec_res = self.exec(prep_res)
                break
            except Exception as e:
                self.cur_retry += 1
                if self.cur_retry >= self.max_retries:
                    exec_res = self.exec_fallback(prep_res, e)
                    break
                else:
                    logger.warning(f"Node {self.name} exec failed (attempt {self.cur_retry}/{self.max_retries}): {e}")
                    if self.wait > 0:
                        time.sleep(self.wait)
        
        # Step 3: Post
        action = self.post(shared, prep_res, exec_res)
        return action if action is not None else "default"
    
    def __rshift__(self, other: 'Node') -> 'Node':
        """
        Connect nodes with default transition: node_a >> node_b
        """
        self._transitions["default"] = other
        return other
    
    def __sub__(self, action: str):
        """
        Start named transition: node_a - "action" >> node_b
        """
        return _Transition(self, action)
    
    def __repr__(self):
        return f"<Node: {self.name}>"


class _Transition:
    """Helper class for named transitions."""
    
    def __init__(self, source: Node, action: str):
        self.source = source
        self.action = action
    
    def __rshift__(self, target: Node) -> Node:
        """Complete the transition: source - "action" >> target"""
        self.source._transitions[self.action] = target
        return target


# Import utilities
from utils.llm_wrapper import get_default_llm_wrapper
import yaml

class ExtractRequirementsNode(Node):
    """Extracts structured requirements from job descriptions using LLM."""
    
    def __init__(self, name: str = "ExtractRequirements", max_retries: int = 3, wait: int = 10):
        super().__init__(name, max_retries, wait)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> str:
        """Read job description from shared store."""
        job_description = shared.get('job_description', '')
        if not job_description:
            raise ValueError("No job description found in shared store")
        return job_description
    
    def exec(self, prep_res: str) -> Dict[str, Any]:
        """Extract requirements using LLM."""
        job_description = prep_res
        
        # System prompt defining the role
        system_prompt = """You are an expert HR analyst and senior technical recruiter with deep understanding of job requirements across various industries. Your task is to extract and structure job requirements from job descriptions into a standardized YAML format."""
        
        # Create the extraction prompt with one-shot example
        prompt = self._create_extraction_prompt(job_description)
        
        # Call LLM with structured output (synchronous)
        requirements = self.llm.call_llm_structured_sync(
            prompt=prompt,
            system_prompt=system_prompt,
            output_format="yaml",
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=3000
        )
        
        # Validate the extracted requirements
        self._validate_requirements(requirements)
        
        return requirements
    
    def exec_fallback(self, prep_res: str, exc: Exception) -> Dict[str, Any]:
        """Return empty requirements on failure."""
        logger.error(f"Failed to extract requirements after all retries: {exc}")
        return {
            'extraction_failed': True,
            'error': str(exc),
            'role_summary': {'title': 'Unknown'},
            'hard_requirements': {},
            'soft_requirements': {},
            'responsibilities': {}
        }
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> Optional[str]:
        """Store extracted requirements in shared store."""
        if exec_res.get('extraction_failed'):
            shared['job_requirements_structured'] = None
            shared['extraction_status'] = 'failed'
            shared['extraction_error'] = exec_res.get('error')
            return "failed"
        else:
            shared['job_requirements_structured'] = exec_res
            shared['extraction_status'] = 'success'
            return "success"
    
    def _create_extraction_prompt(self, job_description: str) -> str:
        """Create the extraction prompt with one-shot example."""
        return f"""Extract the job requirements from the following job description and structure them in YAML format.

IMPORTANT: Your response must be ONLY valid YAML with no additional text or explanations.

Here's an example of the expected format:

```yaml
role_summary:
  title: "Senior Software Engineer"
  company: "DeepMind"
  location: "London, UK"
  type: "Full-time"
  level: "Senior"

hard_requirements:
  education:
    - "Bachelor's degree in Computer Science or related field"
    - "Master's degree preferred"
  experience:
    years_required: 5
    specific_experience:
      - "5+ years of software engineering experience"
      - "3+ years with distributed systems"
      - "Experience with machine learning infrastructure"
  technical_skills:
    programming_languages:
      - "Python"
      - "C++"
      - "Go"
    technologies:
      - "Kubernetes"
      - "TensorFlow"
      - "Cloud platforms (GCP/AWS)"
    concepts:
      - "Distributed systems"
      - "Machine learning"
      - "System design"

soft_requirements:
  skills:
    - "Strong communication skills"
    - "Team collaboration"
    - "Problem-solving ability"
    - "Leadership experience"
  traits:
    - "Self-motivated"
    - "Detail-oriented"
    - "Adaptable to changing priorities"

nice_to_have:
  certifications:
    - "Cloud certifications (GCP/AWS)"
  experience:
    - "Contributing to open source projects"
    - "Publishing research papers"
  skills:
    - "Experience with JAX"
    - "Knowledge of reinforcement learning"

responsibilities:
  primary:
    - "Design and implement scalable ML infrastructure"
    - "Lead technical projects and mentor junior engineers"
    - "Collaborate with research teams"
  secondary:
    - "Participate in code reviews"
    - "Contribute to technical documentation"
    - "Present at internal tech talks"

compensation_benefits:
  salary_range: "Competitive"
  benefits:
    - "Health insurance"
    - "Stock options"
    - "Learning budget"
    - "Flexible working hours"
  perks:
    - "Remote work options"
    - "Conference attendance"
```

Now extract requirements from this job description:

{job_description}

Remember: Respond with ONLY the YAML structure, no additional text."""
    
    def _validate_requirements(self, requirements: Dict[str, Any]) -> None:
        """Validate that extracted requirements have expected structure."""
        required_sections = ['role_summary', 'hard_requirements', 'responsibilities']
        
        for section in required_sections:
            if section not in requirements:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate role_summary
        if 'title' not in requirements['role_summary']:
            raise ValueError("Missing job title in role_summary")
        
        # Validate hard_requirements
        hard_reqs = requirements['hard_requirements']
        if not any(key in hard_reqs for key in ['education', 'experience', 'technical_skills']):
            raise ValueError("Hard requirements must include at least one of: education, experience, technical_skills")
        
        logger.info(f"Successfully validated requirements for: {requirements['role_summary']['title']}")


class RequirementMappingNode(Node):
    """Maps candidate experience to job requirements."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement requirement mapping logic
        pass


class StrengthAssessmentNode(Node):
    """Assesses candidate strengths relative to requirements."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement strength assessment logic
        pass


class GapAnalysisNode(Node):
    """Identifies gaps between candidate profile and requirements."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement gap analysis logic
        pass


class DecideActionNode(Node):
    """Decides what research actions to take."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement action decision logic
        pass


class CompanyResearchNode(Node):
    """Researches company information."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement company research logic
        pass


class SuitabilityScoringNode(Node):
    """Scores candidate suitability for the role."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement suitability scoring logic
        pass


class ExperiencePrioritizationNode(Node):
    """Prioritizes experiences to highlight."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement experience prioritization logic
        pass


class NarrativeStrategyNode(Node):
    """Develops narrative strategy for application."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement narrative strategy logic
        pass


class CVGenerationNode(Node):
    """Generates tailored CV."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement CV generation logic
        pass


class CoverLetterNode(Node):
    """Generates tailored cover letter."""
    
    def exec(self, prep_res: Any) -> Any:
        # TODO: Implement cover letter generation logic
        pass