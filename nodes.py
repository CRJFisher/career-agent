"""
PocketFlow nodes for career application agent.

This module implements the nodes for the career application orchestration system.
Each node represents a discrete unit of work in the job application process.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class Node(ABC):
    """Base class for all nodes in the PocketFlow framework."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def execute(self, store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the node's logic with access to shared store."""
        pass
    
    def __repr__(self):
        return f"<Node: {self.name}>"


# Import utilities
from utils.llm_wrapper import get_default_llm_wrapper
import yaml
import logging

logger = logging.getLogger(__name__)


class ExtractRequirementsNode(Node):
    """Extracts structured requirements from job descriptions using LLM."""
    
    def __init__(self, name: str = "ExtractRequirements"):
        super().__init__(name)
        self.llm = get_default_llm_wrapper()
        self.job_description = None
        self.max_retries = 3
    
    async def execute(self, store: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirements extraction from job description."""
        # Get job description from store
        self.job_description = store.get('job_description', '')
        if not self.job_description:
            raise ValueError("No job description found in store")
        
        # System prompt defining the role
        system_prompt = """You are an expert HR analyst and senior technical recruiter with deep understanding of job requirements across various industries. Your task is to extract and structure job requirements from job descriptions into a standardized YAML format."""
        
        # Create the extraction prompt with one-shot example
        prompt = self._create_extraction_prompt()
        
        # Call LLM with structured output
        try:
            requirements = await self.llm.call_llm_structured(
                prompt=prompt,
                system_prompt=system_prompt,
                output_format="yaml",
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=3000,
                retry_on_parse_error=True,
                max_retries=self.max_retries
            )
            
            # Validate the extracted requirements
            self._validate_requirements(requirements)
            
            # Store the structured requirements
            return {
                'job_requirements_structured': requirements,
                'extraction_status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract requirements: {e}")
            return {
                'job_requirements_structured': None,
                'extraction_status': 'failed',
                'extraction_error': str(e)
            }
    
    def _create_extraction_prompt(self) -> str:
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

{self.job_description}

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
    pass


class StrengthAssessmentNode(Node):
    """Assesses candidate strengths relative to requirements."""
    pass


class GapAnalysisNode(Node):
    """Identifies gaps between candidate profile and requirements."""
    pass


class DecideActionNode(Node):
    """Decides what research actions to take."""
    pass


class CompanyResearchNode(Node):
    """Researches company information."""
    pass


class SuitabilityScoringNode(Node):
    """Scores candidate suitability for the role."""
    pass


class ExperiencePrioritizationNode(Node):
    """Prioritizes experiences to highlight."""
    pass


class NarrativeStrategyNode(Node):
    """Develops narrative strategy for application."""
    pass


class CVGenerationNode(Node):
    """Generates tailored CV."""
    pass


class CoverLetterNode(Node):
    """Generates tailored cover letter."""
    pass