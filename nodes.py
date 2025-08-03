"""
Career application agent nodes.

This module implements the application-specific nodes for the career application
orchestration system. Each node represents a discrete unit of work in the job
application process.

All nodes extend PocketFlow's base Node class and implement:
- prep(shared): Read and preprocess data from shared store
- exec(prep_res): Execute compute logic (mainly LLM calls)
- post(shared, prep_res, exec_res): Write results and return action
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import yaml
import os
from pathlib import Path
from pocketflow import Node, BatchNode
from utils.llm_wrapper import get_default_llm_wrapper

logger = logging.getLogger(__name__)


class ExtractRequirementsNode(Node):
    """
    Parses job descriptions to extract structured requirements.
    
    This node takes a job description and uses an LLM to extract key requirements
    including technical skills, experience levels, and other qualifications.
    """
    
    def __init__(self):
        super().__init__(max_retries=3, wait=2)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> str:
        """Extract job description from shared store."""
        job_description = shared.get("job_description", "")
        if not job_description:
            raise ValueError("No job description found in shared store")
        return job_description
    
    def exec(self, job_description: str) -> Dict[str, Any]:
        """Use LLM to extract requirements from job description."""
        prompt = f"""
        Extract structured requirements from this job description:
        
        {job_description}
        
        Return a YAML structure with:
        - required_skills: List of required technical skills
        - preferred_skills: List of nice-to-have skills
        - experience_years: Required years of experience
        - education: Required education level
        - responsibilities: Key job responsibilities
        - company_culture: Any mentioned culture/values
        """
        
        return self.llm.call_llm_structured_sync(
            prompt=prompt,
            output_format="yaml",
            model="claude-3-opus"
        )
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> Optional[str]:
        """Store extracted requirements in shared store."""
        shared["requirements"] = exec_res
        logger.info(f"Extracted {len(exec_res.get('required_skills', []))} required skills")
        return "default"


class RequirementMappingNode(Node):
    """
    Maps job requirements to candidate's experience using RAG pattern.
    
    Implements a retrieval-augmented approach where it searches the career
    database for relevant evidence that maps to each job requirement.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> tuple:
        """Get requirements and career database."""
        # Note: The task expects 'job_requirements_structured' but we're using 'requirements'
        # This is more consistent with our refactored code
        requirements = shared.get("requirements", {})
        career_db = shared.get("career_database", {})
        
        if not requirements:
            raise ValueError("No requirements found in shared store")
        if not career_db:
            raise ValueError("No career database found in shared store")
            
        return requirements, career_db
    
    def exec(self, inputs: tuple) -> Dict[str, Any]:
        """Map requirements to experience using keyword matching."""
        requirements, career_db = inputs
        
        # Initialize mapping structure
        requirement_mapping_raw = {}
        
        # Extract all searchable text from career database
        searchable_content = self._extract_searchable_content(career_db)
        
        # Map each requirement category
        for req_category, req_items in requirements.items():
            if isinstance(req_items, list):
                # For list items (skills, etc.), search for each item
                requirement_mapping_raw[req_category] = {}
                for item in req_items:
                    evidence = self._search_for_evidence(
                        str(item), 
                        searchable_content
                    )
                    if evidence:
                        requirement_mapping_raw[req_category][item] = evidence
            elif isinstance(req_items, dict):
                # For nested structures, process recursively
                requirement_mapping_raw[req_category] = {}
                for key, value in req_items.items():
                    evidence = self._search_for_evidence(
                        f"{key} {value}", 
                        searchable_content
                    )
                    if evidence:
                        requirement_mapping_raw[req_category][key] = evidence
            else:
                # For single values, search directly
                evidence = self._search_for_evidence(
                    str(req_items), 
                    searchable_content
                )
                if evidence:
                    requirement_mapping_raw[req_category] = evidence
        
        # Calculate coverage score
        total_requirements = self._count_requirements(requirements)
        mapped_requirements = self._count_mapped_requirements(requirement_mapping_raw)
        coverage_score = mapped_requirements / total_requirements if total_requirements > 0 else 0.0
        
        return {
            "requirement_mapping_raw": requirement_mapping_raw,
            "coverage_score": coverage_score,
            "total_requirements": total_requirements,
            "mapped_requirements": mapped_requirements
        }
    
    def post(self, shared: Dict[str, Any], prep_res: tuple, exec_res: Dict[str, Any]) -> Optional[str]:
        """Store requirement mappings in shared store."""
        shared["requirement_mapping_raw"] = exec_res["requirement_mapping_raw"]
        shared["coverage_score"] = exec_res["coverage_score"]
        
        logger.info(f"Mapped {exec_res['mapped_requirements']} out of {exec_res['total_requirements']} requirements")
        logger.info(f"Coverage score: {exec_res['coverage_score']:.2%}")
        
        return "default"
    
    def _extract_searchable_content(self, career_db: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all searchable content from career database."""
        searchable_content = []
        
        # Extract from experience section
        if "experience" in career_db:
            for exp in career_db["experience"]:
                content = {
                    "type": "experience",
                    "title": exp.get("title", ""),
                    "company": exp.get("company", ""),
                    "text": " ".join([
                        exp.get("title", ""),
                        exp.get("company", ""),
                        exp.get("description", ""),
                        " ".join(exp.get("achievements", [])),
                        " ".join(exp.get("technologies", []))
                    ]),
                    "source": exp
                }
                searchable_content.append(content)
                
                # Also extract from nested projects
                if "projects" in exp:
                    for proj in exp["projects"]:
                        proj_content = {
                            "type": "experience_project",
                            "title": proj.get("title", ""),
                            "parent_role": exp.get("title", ""),
                            "text": " ".join([
                                proj.get("title", ""),
                                proj.get("description", ""),
                                " ".join(proj.get("achievements", [])),
                                " ".join(proj.get("technologies", []))
                            ]),
                            "source": proj
                        }
                        searchable_content.append(proj_content)
        
        # Extract from projects section
        if "projects" in career_db:
            for proj in career_db["projects"]:
                content = {
                    "type": "project",
                    "title": proj.get("name", ""),
                    "text": " ".join([
                        proj.get("name", ""),
                        proj.get("description", ""),
                        " ".join(proj.get("outcomes", [])),
                        " ".join(proj.get("technologies", []))
                    ]),
                    "source": proj
                }
                searchable_content.append(content)
        
        # Extract from skills
        if "skills" in career_db:
            skills = career_db["skills"]
            all_skills = []
            for category, items in skills.items():
                if isinstance(items, list):
                    all_skills.extend(items)
            
            if all_skills:
                content = {
                    "type": "skills",
                    "title": "Skills",
                    "text": " ".join(all_skills),
                    "source": skills
                }
                searchable_content.append(content)
        
        return searchable_content
    
    def _search_for_evidence(self, requirement: str, searchable_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search for evidence matching a requirement using keyword matching."""
        evidence = []
        
        # Convert requirement to lowercase for case-insensitive matching
        req_lower = requirement.lower()
        req_words = set(req_lower.split())
        
        for content in searchable_content:
            text_lower = content["text"].lower()
            
            # Check for exact phrase match
            if req_lower in text_lower:
                evidence.append({
                    "type": content["type"],
                    "title": content["title"],
                    "match_type": "exact",
                    "source": content["source"]
                })
                continue
            
            # Check for word-based matching
            text_words = set(text_lower.split())
            common_words = req_words.intersection(text_words)
            
            if len(common_words) >= len(req_words) * 0.5:  # At least 50% word match
                evidence.append({
                    "type": content["type"],
                    "title": content["title"],
                    "match_type": "partial",
                    "match_score": len(common_words) / len(req_words),
                    "source": content["source"]
                })
        
        # Sort by match quality (exact matches first, then by match score)
        evidence.sort(key=lambda x: (
            0 if x["match_type"] == "exact" else 1,
            -x.get("match_score", 0)
        ))
        
        return evidence[:5]  # Return top 5 matches
    
    def _count_requirements(self, requirements: Dict[str, Any]) -> int:
        """Count total number of requirements."""
        count = 0
        for value in requirements.values():
            if isinstance(value, list):
                count += len(value)
            elif isinstance(value, dict):
                count += len(value)
            else:
                count += 1
        return count
    
    def _count_mapped_requirements(self, mapping: Dict[str, Any]) -> int:
        """Count number of successfully mapped requirements."""
        count = 0
        for value in mapping.values():
            if isinstance(value, dict):
                count += len([v for v in value.values() if v])
            elif isinstance(value, list) and value:
                count += 1
            elif value:
                count += 1
        return count


class StrengthAssessmentNode(Node):
    """
    Evaluates the strength of requirement-to-evidence mappings using LLM.
    
    This node uses an LLM to assess how well each piece of evidence demonstrates
    the required skill or qualification, assigning HIGH, MEDIUM, or LOW scores.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Get requirement mapping from shared store."""
        mapping = shared.get("requirement_mapping_raw", {})
        
        if not mapping:
            raise ValueError("No requirement mapping found in shared store")
            
        return mapping
    
    def exec(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Assess strength of each requirement-evidence mapping."""
        assessed_mapping = {}
        
        for req_category, req_items in mapping.items():
            if isinstance(req_items, dict):
                # Handle dict-type requirements (skills, responsibilities)
                assessed_mapping[req_category] = {}
                
                for req_name, evidence_list in req_items.items():
                    if evidence_list:
                        assessed_evidence = []
                        for evidence in evidence_list:
                            # Assess each piece of evidence
                            strength = self._assess_evidence_strength(
                                req_name, evidence
                            )
                            evidence_with_strength = evidence.copy()
                            evidence_with_strength["strength"] = strength
                            assessed_evidence.append(evidence_with_strength)
                        
                        assessed_mapping[req_category][req_name] = assessed_evidence
                    else:
                        # No evidence found
                        assessed_mapping[req_category][req_name] = []
                        
            elif isinstance(req_items, list):
                # Handle list-type requirements (single value mapped to evidence)
                assessed_evidence = []
                for evidence in req_items:
                    strength = self._assess_evidence_strength(
                        req_category, evidence
                    )
                    evidence_with_strength = evidence.copy()
                    evidence_with_strength["strength"] = strength
                    assessed_evidence.append(evidence_with_strength)
                
                assessed_mapping[req_category] = assessed_evidence
        
        return {
            "requirement_mapping_assessed": assessed_mapping
        }
    
    def _assess_evidence_strength(self, requirement: str, evidence: Dict[str, Any]) -> str:
        """Use LLM to assess how well evidence demonstrates the requirement."""
        prompt = f"""Assess how strongly this evidence demonstrates the requirement.

Requirement: {requirement}

Evidence Type: {evidence.get('type', 'unknown')}
Evidence Title: {evidence.get('title', 'N/A')}
Match Type: {evidence.get('match_type', 'unknown')}

Scoring Criteria:
- HIGH: Direct, powerful demonstration of the exact skill/requirement
- MEDIUM: Related experience that partially demonstrates the requirement
- LOW: Weak or indirect connection to the requirement

Respond with only one word: HIGH, MEDIUM, or LOW"""

        try:
            response = self.llm.call_llm_sync(prompt)
            strength = response.strip().upper()
            
            # Validate response
            if strength not in ["HIGH", "MEDIUM", "LOW"]:
                logger.warning(f"Invalid strength score: {strength}, defaulting to MEDIUM")
                return "MEDIUM"
                
            return strength
        except Exception as e:
            logger.error(f"Error assessing evidence strength: {e}")
            return "MEDIUM"  # Default to MEDIUM on error
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Dict[str, Any]) -> str:
        """Store assessed mapping in shared store."""
        shared["requirement_mapping_assessed"] = exec_res["requirement_mapping_assessed"]
        return "default"


class GapAnalysisNode(Node):
    """
    Identifies gaps in requirements and generates mitigation strategies.
    
    This node analyzes the assessed mapping to find must-have requirements
    with weak or missing evidence, then generates strategic approaches to
    address these gaps in applications and interviews.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get assessed mapping and original requirements."""
        assessed_mapping = shared.get("requirement_mapping_assessed", {})
        requirements = shared.get("requirements", {})
        
        if not assessed_mapping:
            raise ValueError("No assessed mapping found in shared store")
        if not requirements:
            raise ValueError("No requirements found in shared store")
            
        return assessed_mapping, requirements
    
    def exec(self, inputs: Tuple[Dict[str, Any], Dict[str, Any]]) -> Dict[str, Any]:
        """Identify gaps and generate mitigation strategies."""
        assessed_mapping, requirements = inputs
        
        # Identify gaps
        gaps = self._identify_gaps(assessed_mapping, requirements)
        
        # Generate mitigation strategies for each gap
        gaps_with_strategies = []
        for gap in gaps:
            strategy = self._generate_mitigation_strategy(gap)
            gap_with_strategy = gap.copy()
            gap_with_strategy["mitigation_strategy"] = strategy
            gaps_with_strategies.append(gap_with_strategy)
        
        # Create final mapping (for downstream use)
        final_mapping = self._create_final_mapping(assessed_mapping)
        
        return {
            "requirement_mapping_final": final_mapping,
            "gaps": gaps_with_strategies
        }
    
    def _identify_gaps(self, assessed_mapping: Dict[str, Any], 
                      requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify must-have requirements with weak or no evidence."""
        gaps = []
        
        # Check required skills (typically must-have)
        if "required_skills" in requirements and "required_skills" in assessed_mapping:
            for skill in requirements["required_skills"]:
                evidence = assessed_mapping["required_skills"].get(skill, [])
                
                if not evidence:
                    # No evidence at all
                    gaps.append({
                        "requirement": skill,
                        "category": "required_skills",
                        "gap_type": "missing",
                        "evidence": []
                    })
                elif all(e.get("strength") == "LOW" for e in evidence):
                    # Only weak evidence
                    gaps.append({
                        "requirement": skill,
                        "category": "required_skills",
                        "gap_type": "weak",
                        "evidence": evidence
                    })
        
        # Check other must-have categories (could be configured)
        must_have_categories = ["experience_years", "education", "certifications"]
        
        for category in must_have_categories:
            if category in requirements and category in assessed_mapping:
                evidence = assessed_mapping.get(category, [])
                
                if isinstance(evidence, list):
                    if not evidence:
                        gaps.append({
                            "requirement": requirements[category],
                            "category": category,
                            "gap_type": "missing",
                            "evidence": []
                        })
                    elif all(e.get("strength") == "LOW" for e in evidence):
                        gaps.append({
                            "requirement": requirements[category],
                            "category": category,
                            "gap_type": "weak",
                            "evidence": evidence
                        })
        
        return gaps
    
    def _generate_mitigation_strategy(self, gap: Dict[str, Any]) -> str:
        """Use LLM to generate mitigation strategy for a gap."""
        gap_type = gap["gap_type"]
        requirement = gap["requirement"]
        category = gap["category"]
        
        prompt = f"""Generate a mitigation strategy for this requirement gap.

Requirement: {requirement} ({category})
Gap Type: {gap_type} ({"no evidence found" if gap_type == "missing" else "only weak evidence"})

Create a brief strategy (2-3 sentences) that:
1. Acknowledges the gap honestly
2. Highlights transferable skills or related experience
3. Shows enthusiasm to learn/develop this skill
4. Focuses on growth potential

Be specific and strategic. Avoid generic statements."""

        try:
            strategy = self.llm.call_llm_sync(prompt)
            return strategy.strip()
        except Exception as e:
            logger.error(f"Error generating mitigation strategy: {e}")
            return "Highlight transferable skills and demonstrate strong learning ability and enthusiasm for this area."
    
    def _create_final_mapping(self, assessed_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Create final mapping with gap indicators."""
        final_mapping = {}
        
        for category, items in assessed_mapping.items():
            if isinstance(items, dict):
                final_mapping[category] = {}
                for req, evidence in items.items():
                    # Mark as gap if no evidence or all LOW
                    is_gap = (not evidence or 
                             all(e.get("strength") == "LOW" for e in evidence))
                    
                    final_mapping[category][req] = {
                        "evidence": evidence,
                        "is_gap": is_gap,
                        "strength_summary": self._summarize_strength(evidence)
                    }
            else:
                # Single value requirements
                is_gap = (not items or 
                         all(e.get("strength") == "LOW" for e in items))
                
                final_mapping[category] = {
                    "evidence": items,
                    "is_gap": is_gap,
                    "strength_summary": self._summarize_strength(items)
                }
        
        return final_mapping
    
    def _summarize_strength(self, evidence: List[Dict[str, Any]]) -> str:
        """Summarize overall strength of evidence."""
        if not evidence:
            return "NONE"
        
        strengths = [e.get("strength", "MEDIUM") for e in evidence]
        
        if "HIGH" in strengths:
            return "HIGH"
        elif "MEDIUM" in strengths:
            return "MEDIUM"
        else:
            return "LOW"
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Dict[str, Any]) -> str:
        """Store results in shared store."""
        shared["requirement_mapping_final"] = exec_res["requirement_mapping_final"]
        shared["gaps"] = exec_res["gaps"]
        return "default"


# Workflow Management Nodes

class SaveCheckpointNode(Node):
    """
    Saves workflow state to checkpoint files for user review.
    
    Exports specific data to user-editable YAML files and pauses
    the workflow for manual review and editing. Supports backup
    of previous checkpoints and configurable export templates.
    """
    
    def __init__(self, max_retries: int = 3, wait: float = 1.0):
        """
        Initialize SaveCheckpointNode.
        
        Args:
            max_retries: Maximum retry attempts for file operations
            wait: Wait time between retries
        """
        super().__init__(max_retries, wait)
        self.checkpoint_dir = Path("checkpoints")
        self.output_dir = Path("outputs")
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what to save based on flow context and parameters."""
        from datetime import datetime
        
        # Get configuration from params
        flow_name = self.params.get("flow_name", shared.get("flow_name", "workflow"))
        checkpoint_name = self.params.get("checkpoint_name", "checkpoint")
        checkpoint_data = self.params.get("checkpoint_data", [])
        output_file = self.params.get("output_file", f"{flow_name}_output.yaml")
        user_message = self.params.get("user_message", None)
        
        # Create export configuration
        export_config = {
            "flow_name": flow_name,
            "checkpoint_name": checkpoint_name,
            "timestamp": datetime.now(),
            "checkpoint_data": checkpoint_data,
            "output_file": output_file,
            "user_message": user_message,
            "node_class": self.__class__.__name__,
            "format_version": "1.0"
        }
        
        # Add flow-specific export fields if not explicitly provided
        if not checkpoint_data:
            if flow_name == "analysis":
                export_config["checkpoint_data"] = [
                    "requirements",
                    "requirement_mapping_raw",
                    "requirement_mapping_assessed", 
                    "requirement_mapping_final",
                    "gaps",
                    "coverage_score"
                ]
            elif flow_name == "narrative":
                export_config["checkpoint_data"] = [
                    "prioritized_experiences",
                    "narrative_strategy",
                    "suitability_assessment",
                    "requirements",
                    "job_title",
                    "company_name"
                ]
            elif flow_name == "experience_db":
                export_config["checkpoint_data"] = [
                    "document_sources",
                    "extracted_experiences",
                    "extraction_summary"
                ]
        
        return export_config
    
    def exec(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save checkpoint and generate user-editable files."""
        import yaml
        import shutil
        from datetime import datetime
        
        # Create directories
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create checkpoint subdirectory for this flow
        flow_checkpoint_dir = self.checkpoint_dir / config["flow_name"]
        flow_checkpoint_dir.mkdir(exist_ok=True)
        
        # Generate filenames
        timestamp_str = config["timestamp"].strftime("%Y%m%d_%H%M%S")
        checkpoint_filename = f"{config['checkpoint_name']}_{timestamp_str}.yaml"
        checkpoint_path = flow_checkpoint_dir / checkpoint_filename
        output_path = self.output_dir / config["output_file"]
        
        # Backup existing checkpoint if it exists
        latest_link = flow_checkpoint_dir / f"{config['checkpoint_name']}_latest.yaml"
        if latest_link.exists():
            try:
                backup_path = latest_link.with_suffix('.yaml.bak')
                shutil.copy2(latest_link.resolve(), backup_path)
                logger.info(f"Backed up existing checkpoint to: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not backup checkpoint: {e}")
        
        return {
            "checkpoint_path": checkpoint_path,
            "output_path": output_path,
            "latest_link": latest_link,
            "config": config,
            "timestamp_str": timestamp_str
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> str:
        """Save checkpoint files and generate user-editable output."""
        import yaml
        from datetime import datetime
        
        config = exec_res["config"]
        
        # Prepare checkpoint data
        checkpoint_data = {
            "metadata": {
                "checkpoint_name": config["checkpoint_name"],
                "flow_name": config["flow_name"],
                "timestamp": config["timestamp"].isoformat(),
                "node_class": config["node_class"],
                "format_version": config["format_version"]
            },
            "shared_state": {},
            "recovery_info": {
                "next_node": shared.get("next_node", "unknown"),
                "can_resume": True,
                "required_state_keys": config["checkpoint_data"]
            }
        }
        
        # Copy specified fields to checkpoint
        for field in config["checkpoint_data"]:
            if field in shared:
                checkpoint_data["shared_state"][field] = shared[field]
        
        # Add flow configuration and stats
        checkpoint_data["shared_state"]["flow_config"] = shared.get("flow_config", {})
        checkpoint_data["shared_state"]["flow_progress"] = shared.get("flow_progress", {})
        
        # Save full checkpoint
        try:
            with open(exec_res["checkpoint_path"], 'w', encoding='utf-8') as f:
                yaml.dump(checkpoint_data, f, default_flow_style=False, 
                         sort_keys=False, allow_unicode=True, width=120)
            
            # Update latest symlink
            latest_link = exec_res["latest_link"]
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(exec_res["checkpoint_path"].name)
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise
        
        # Generate user-editable output with instructions
        output_data = self._generate_user_output(shared, config)
        
        # Save user-editable file
        try:
            with open(exec_res["output_path"], 'w', encoding='utf-8') as f:
                # Write header comments manually for better formatting
                f.write(f"# {'-' * 70}\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Flow: {config['flow_name']}\n")
                f.write(f"# Checkpoint: {config['checkpoint_name']}\n")
                f.write(f"# {'-' * 70}\n")
                
                if config["user_message"]:
                    f.write("#\n")
                    for line in config["user_message"].strip().split('\n'):
                        f.write(f"# {line}\n")
                    f.write("#\n")
                else:
                    f.write("#\n")
                    f.write("# INSTRUCTIONS:\n")
                    f.write("# 1. Review the data below\n")
                    f.write("# 2. Make any necessary edits\n")
                    f.write("# 3. Save this file when complete\n")
                    f.write("# 4. Resume the workflow to continue processing\n")
                    f.write("#\n")
                
                f.write(f"# {'-' * 70}\n\n")
                
                # Write the data
                yaml.dump(output_data, f, default_flow_style=False, 
                         sort_keys=False, allow_unicode=True, width=120)
        
        except Exception as e:
            logger.error(f"Failed to save user output: {e}")
            raise
        
        # Update shared store with checkpoint info
        shared["last_checkpoint"] = {
            "name": config["checkpoint_name"],
            "path": str(exec_res["checkpoint_path"]),
            "timestamp": config["timestamp"].isoformat(),
            "output_file": str(exec_res["output_path"])
        }
        
        # Log summary
        logger.info("=" * 60)
        logger.info(f"✓ Checkpoint saved: {config['checkpoint_name']}")
        logger.info(f"  Checkpoint: {exec_res['checkpoint_path']}")
        logger.info(f"  User file: {exec_res['output_path']}")
        logger.info("=" * 60)
        
        # Return action based on flow requirements
        # Some flows may want to continue, others pause
        return self.params.get("action", "continue")
    
    def _generate_user_output(self, shared: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate user-editable output based on flow type."""
        output = {}
        
        # Export specified fields
        for field in config["checkpoint_data"]:
            if field in shared:
                output[field] = shared[field]
        
        # Add flow-specific formatting or templates
        if config["flow_name"] == "analysis":
            # Format requirement mappings for easier editing
            if "requirement_mapping_final" in output:
                formatted_mappings = []
                for req_id, mapping in output["requirement_mapping_final"].items():
                    formatted_mappings.append({
                        "requirement_id": req_id,
                        "requirement": mapping.get("requirement", ""),
                        "evidence": mapping.get("evidence", []),
                        "strength": mapping.get("strength", ""),
                        "notes": mapping.get("notes", "")
                    })
                output["requirement_mappings"] = formatted_mappings
                del output["requirement_mapping_final"]
        
        elif config["flow_name"] == "narrative":
            # Add helpful structure for narrative editing
            if "narrative_strategy" in output:
                strategy = output["narrative_strategy"]
                output["narrative_strategy"] = {
                    "must_tell_experiences": strategy.get("must_tell_experiences", []),
                    "career_arc": strategy.get("career_arc", {}),
                    "key_messages": strategy.get("key_messages", []),
                    "evidence_stories": strategy.get("evidence_stories", []),
                    "differentiators": strategy.get("differentiators", [])
                }
        
        return output


class LoadCheckpointNode(Node):
    """
    Loads checkpoint and merges user edits to resume workflow.
    
    Reads checkpoint files and user-edited output files, validating
    integrity and merging changes back into the shared store. Supports
    automatic checkpoint discovery and modification detection.
    """
    
    def __init__(self, checkpoint_name: str = None, auto_detect: bool = True, 
                 max_retries: int = 3, wait: float = 1.0):
        """
        Initialize LoadCheckpointNode.
        
        Args:
            checkpoint_name: Specific checkpoint to load (optional)
            auto_detect: Whether to auto-detect latest checkpoint
            max_retries: Maximum retry attempts for file operations
            wait: Wait time between retries
        """
        super().__init__(max_retries, wait)
        self.checkpoint_name = checkpoint_name
        self.auto_detect = auto_detect
        self.checkpoint_dir = Path("checkpoints")
        self.output_dir = Path("outputs")
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which checkpoint to load."""
        from datetime import datetime
        
        # Get flow name from params or shared
        flow_name = self.params.get("flow_name", shared.get("flow_name", "workflow"))
        checkpoint_name = self.params.get("checkpoint_name", self.checkpoint_name)
        
        # Find checkpoint file
        if checkpoint_name:
            checkpoint_path = self._find_specific_checkpoint(checkpoint_name, flow_name)
        elif self.auto_detect:
            checkpoint_path = self._find_latest_checkpoint(flow_name)
        else:
            raise ValueError("No checkpoint specified and auto_detect is False")
        
        return {
            "checkpoint_path": checkpoint_path,
            "flow_name": flow_name,
            "load_timestamp": datetime.now()
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """Load checkpoint and merge with user edits."""
        import yaml
        from datetime import datetime
        
        checkpoint_path = prep_res["checkpoint_path"]
        
        # Load checkpoint data
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load checkpoint {checkpoint_path}: {e}")
        
        # Validate checkpoint
        self._validate_checkpoint(checkpoint_data)
        
        # Extract metadata and shared state
        metadata = checkpoint_data.get("metadata", {})
        shared_state = checkpoint_data.get("shared_state", {})
        recovery_info = checkpoint_data.get("recovery_info", {})
        
        # Find and load user edits
        user_edits = self._load_user_edits(shared_state, metadata)
        
        # Merge checkpoint and user edits
        merged_state = self._merge_checkpoint_and_edits(shared_state, user_edits)
        
        # Detect modifications
        modifications = self._detect_modifications(shared_state, merged_state)
        
        return {
            "checkpoint_path": str(checkpoint_path),
            "metadata": metadata,
            "shared_state": shared_state,
            "merged_state": merged_state,
            "user_edits": user_edits,
            "modifications": modifications,
            "recovery_info": recovery_info
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> str:
        """Update shared store with loaded state."""
        # Clear existing state if requested
        if self.params.get("clear_existing", False):
            shared.clear()
        
        # Apply merged state to shared store
        shared.update(exec_res["merged_state"])
        
        # Add checkpoint resumption metadata
        shared["resumed_from_checkpoint"] = {
            "checkpoint_name": exec_res["metadata"].get("checkpoint_name"),
            "checkpoint_path": exec_res["checkpoint_path"],
            "timestamp": exec_res["metadata"].get("timestamp"),
            "modifications_count": len(exec_res["modifications"]),
            "modifications": exec_res["modifications"]
        }
        
        # Log resumption details
        logger.info("=" * 60)
        logger.info(f"✓ Resumed from checkpoint: {Path(exec_res['checkpoint_path']).name}")
        logger.info(f"  Flow: {exec_res['metadata'].get('flow_name', 'unknown')}")
        logger.info(f"  Created: {exec_res['metadata'].get('timestamp', 'unknown')}")
        
        if exec_res["modifications"]:
            logger.info(f"  User modifications: {len(exec_res['modifications'])}")
            for mod in exec_res["modifications"][:5]:  # Show first 5
                logger.info(f"    - {mod['path']}: {mod.get('action', 'modified')}")
            if len(exec_res["modifications"]) > 5:
                logger.info(f"    ... and {len(exec_res['modifications']) - 5} more")
        
        logger.info("=" * 60)
        
        # Determine next action from recovery info or params
        next_action = self.params.get("action", 
                                    exec_res["recovery_info"].get("next_action", "continue"))
        return next_action
    
    def _find_latest_checkpoint(self, flow_name: str) -> Path:
        """Find the most recent checkpoint for a flow."""
        # Check flow-specific directory
        flow_checkpoint_dir = self.checkpoint_dir / flow_name
        
        # First check for latest symlink
        if flow_checkpoint_dir.exists():
            latest_links = list(flow_checkpoint_dir.glob("*_latest.yaml"))
            if latest_links:
                # Follow symlink to actual file
                for link in latest_links:
                    if link.exists():
                        return link.resolve()
        
        # Search for checkpoint files
        patterns = [
            f"{flow_name}/*_*.yaml",  # Flow-specific directory
            f"{flow_name}_*.yaml"      # Root checkpoint directory
        ]
        
        all_checkpoints = []
        for pattern in patterns:
            checkpoints = list(self.checkpoint_dir.glob(pattern))
            all_checkpoints.extend(checkpoints)
        
        # Filter out symlinks and backups
        valid_checkpoints = [
            cp for cp in all_checkpoints 
            if not cp.is_symlink() and not cp.name.endswith('.bak')
        ]
        
        if not valid_checkpoints:
            raise FileNotFoundError(f"No checkpoints found for flow: {flow_name}")
        
        # Return most recent by modification time
        return max(valid_checkpoints, key=lambda p: p.stat().st_mtime)
    
    def _find_specific_checkpoint(self, checkpoint_name: str, flow_name: str) -> Path:
        """Find a specific checkpoint by name."""
        # Try exact paths
        exact_paths = [
            self.checkpoint_dir / flow_name / f"{checkpoint_name}.yaml",
            self.checkpoint_dir / flow_name / f"{checkpoint_name}_*.yaml",
            self.checkpoint_dir / f"{checkpoint_name}.yaml",
            self.checkpoint_dir / f"{flow_name}_{checkpoint_name}.yaml"
        ]
        
        for path_pattern in exact_paths:
            if '*' in str(path_pattern):
                matches = list(path_pattern.parent.glob(path_pattern.name))
                if matches:
                    return max(matches, key=lambda p: p.stat().st_mtime)
            elif path_pattern.exists():
                return path_pattern
        
        # Try pattern matching
        patterns = [
            f"**/*{checkpoint_name}*.yaml",
            f"{flow_name}/*{checkpoint_name}*.yaml"
        ]
        
        for pattern in patterns:
            matches = list(self.checkpoint_dir.glob(pattern))
            valid_matches = [
                m for m in matches 
                if not m.is_symlink() and not m.name.endswith('.bak')
            ]
            if valid_matches:
                if len(valid_matches) > 1:
                    logger.warning(f"Multiple checkpoints match '{checkpoint_name}', using most recent")
                return max(valid_matches, key=lambda p: p.stat().st_mtime)
        
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_name}")
    
    def _validate_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """Validate checkpoint integrity and compatibility."""
        from datetime import datetime
        
        # Check required top-level fields
        required_fields = ["metadata", "shared_state"]
        for field in required_fields:
            if field not in checkpoint_data:
                raise ValueError(f"Invalid checkpoint: missing '{field}' field")
        
        metadata = checkpoint_data["metadata"]
        
        # Check format version compatibility
        version = metadata.get("format_version", "0.0")
        if not self._is_version_compatible(version):
            raise ValueError(f"Incompatible checkpoint version: {version} (expected 1.x)")
        
        # Validate metadata fields
        required_metadata = ["checkpoint_name", "flow_name", "timestamp"]
        for field in required_metadata:
            if field not in metadata:
                logger.warning(f"Checkpoint metadata missing '{field}' field")
        
        # Check age of checkpoint
        timestamp_str = metadata.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age = datetime.now() - timestamp
                if age.days > 30:
                    logger.warning(f"Checkpoint is {age.days} days old")
                elif age.days > 7:
                    logger.info(f"Checkpoint is {age.days} days old")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid checkpoint timestamp: {e}")
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if checkpoint version is compatible."""
        try:
            major, minor = map(int, version.split('.'))
            # Compatible with version 1.x
            return major == 1
        except:
            return False
    
    def _load_user_edits(self, shared_state: Dict[str, Any], 
                        metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Load user-edited files associated with checkpoint."""
        user_edits = {}
        
        # Get output file info from checkpoint
        last_checkpoint = shared_state.get("last_checkpoint", {})
        output_file = last_checkpoint.get("output_file")
        
        if output_file and Path(output_file).exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                # Remove comment fields
                if isinstance(content, dict):
                    user_edits = {
                        k: v for k, v in content.items() 
                        if not k.startswith('#')
                    }
                    logger.info(f"Loaded user edits from: {output_file}")
            except Exception as e:
                logger.warning(f"Could not load user edits from {output_file}: {e}")
        
        # Also check standard output location
        flow_name = metadata.get("flow_name", "workflow")
        standard_output = self.output_dir / f"{flow_name}_output.yaml"
        
        if standard_output.exists() and str(standard_output) != output_file:
            try:
                with open(standard_output, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                if isinstance(content, dict):
                    additional_edits = {
                        k: v for k, v in content.items() 
                        if not k.startswith('#')
                    }
                    # Merge, with user_edits taking precedence
                    additional_edits.update(user_edits)
                    user_edits = additional_edits
                    logger.info(f"Also loaded edits from: {standard_output}")
            except Exception as e:
                logger.warning(f"Could not load additional edits: {e}")
        
        return user_edits
    
    def _merge_checkpoint_and_edits(self, checkpoint_state: Dict[str, Any], 
                                   user_edits: Dict[str, Any]) -> Dict[str, Any]:
        """Merge checkpoint data with user edits."""
        # Deep copy checkpoint state
        import copy
        merged = copy.deepcopy(checkpoint_state)
        
        # Apply user edits
        for key, value in user_edits.items():
            if key in merged:
                logger.info(f"Replacing '{key}' with user-edited version")
            else:
                logger.info(f"Adding new field '{key}' from user edits")
            merged[key] = value
        
        return merged
    
    def _detect_modifications(self, original: Dict[str, Any], 
                            modified: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect what the user changed."""
        modifications = []
        
        def deep_compare(path: str, orig: Any, mod: Any) -> None:
            """Recursively compare data structures."""
            if type(orig) != type(mod):
                modifications.append({
                    "path": path,
                    "action": "type_changed",
                    "original_type": type(orig).__name__,
                    "modified_type": type(mod).__name__
                })
                return
            
            if isinstance(orig, dict) and isinstance(mod, dict):
                all_keys = set(orig.keys()) | set(mod.keys())
                for key in all_keys:
                    new_path = f"{path}.{key}" if path else key
                    
                    if key not in orig:
                        modifications.append({
                            "path": new_path,
                            "action": "added",
                            "value": mod[key]
                        })
                    elif key not in mod:
                        modifications.append({
                            "path": new_path,
                            "action": "deleted",
                            "original": orig[key]
                        })
                    else:
                        deep_compare(new_path, orig[key], mod[key])
            
            elif isinstance(orig, list) and isinstance(mod, list):
                if len(orig) != len(mod):
                    modifications.append({
                        "path": path,
                        "action": "list_size_changed",
                        "original_size": len(orig),
                        "modified_size": len(mod)
                    })
                # Compare list items up to min length
                for i in range(min(len(orig), len(mod))):
                    deep_compare(f"{path}[{i}]", orig[i], mod[i])
            
            elif orig != mod:
                modifications.append({
                    "path": path,
                    "action": "modified",
                    "original": orig,
                    "modified": mod
                })
        
        # Start comparison
        deep_compare("", original, modified)
        
        return modifications


class DecideActionNode(Node):
    """
    Cognitive core for the company research agent.
    
    This node implements the Agent pattern's decision-making capability.
    It assesses research progress, determines what information is still needed,
    and selects appropriate tools to continue the research process.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Extract research context from shared store."""
        company_name = shared.get("company_name", "")
        if not company_name:
            raise ValueError("No company name provided for research")
        
        # Initialize research state if not present
        if "research_state" not in shared:
            shared["research_state"] = {
                "searches_performed": [],
                "pages_read": [],
                "information_gathered": {},
                "synthesis_complete": False
            }
        
        # Get or set default research goals
        if "research_goals" not in shared or not shared["research_goals"]:
            shared["research_goals"] = self._default_research_goals()
        
        return {
            "company_name": company_name,
            "job_title": shared.get("job_title", ""),
            "research_goals": shared.get("research_goals", []),
            "research_state": shared["research_state"]
        }
    
    def exec(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to decide next research action."""
        prompt = self._build_agent_prompt(context)
        
        try:
            response = self.llm.call_llm_sync(prompt)
            decision = yaml.safe_load(response)
            
            # Validate response structure
            if not isinstance(decision, dict) or "action" not in decision:
                raise ValueError("Decision missing required fields")
            
            action = decision["action"]
            if not isinstance(action, dict) or "type" not in action:
                raise ValueError("Action missing type field")
            
            return {
                "decision": decision,
                "action_type": action["type"],
                "action_params": action.get("parameters", {})
            }
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML response: {e}")
            # Fallback to basic web search
            return {
                "decision": {
                    "thinking": "Failed to parse response, falling back to web search",
                    "action": {"type": "web_search", "parameters": {"query": context["company_name"]}}
                },
                "action_type": "web_search",
                "action_params": {"query": context["company_name"]}
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> str:
        """Store decision and update research state."""
        shared["last_decision"] = exec_res["decision"]
        shared["next_action"] = exec_res["action_type"]
        shared["action_params"] = exec_res["action_params"]
        
        # Update research state based on action
        action_type = exec_res["action_type"]
        if action_type == "web_search":
            query = exec_res["action_params"].get("query", "")
            if query and query not in shared["research_state"]["searches_performed"]:
                shared["research_state"]["searches_performed"].append(query)
        elif action_type == "read_content":
            url = exec_res["action_params"].get("url", "")
            if url and url not in shared["research_state"]["pages_read"]:
                shared["research_state"]["pages_read"].append(url)
        elif action_type == "synthesize":
            shared["research_state"]["synthesis_complete"] = True
        
        # Return the action type as the node's action
        return action_type
    
    def _build_agent_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive agent prompt."""
        return f"""You are a company research agent gathering information for a job application.

## CONTEXT

Company: {context['company_name']}
Job Title: {context['job_title'] or 'Not specified'}

Research Goals:
{chr(10).join(f'- {goal}' for goal in context['research_goals'])}

Current Research State:
- Searches Performed: {len(context['research_state']['searches_performed'])}
  {chr(10).join(f'  * {s}' for s in context['research_state']['searches_performed'][-5:])}
- Pages Read: {len(context['research_state']['pages_read'])}
  {chr(10).join(f'  * {p}' for p in context['research_state']['pages_read'][-5:])}
- Information Gathered:
  {chr(10).join(f'  * {k}: {len(v)} items' for k, v in context['research_state']['information_gathered'].items())}
- Synthesis Complete: {context['research_state']['synthesis_complete']}

## ACTION SPACE

You have access to these tools:

1. **web_search**: Search the web for information
   - Parameters:
     - query: Search query string
   - Use when: You need to find new information sources
   
2. **read_content**: Read and extract content from a URL
   - Parameters:
     - url: The URL to read
     - focus: What to look for (optional)
   - Use when: You found a promising URL in search results
   
3. **synthesize**: Compile gathered information into insights
   - Parameters: none
   - Use when: You have enough information to meet research goals
   
4. **finish**: Complete the research process
   - Parameters: none
   - Use when: Synthesis is complete or no more useful research possible

## NEXT ACTION

Think through:
1. What information do we still need?
2. Which research goals are not yet addressed?
3. What's the most efficient next step?

Respond in YAML format:

```yaml
thinking: |
  Your reasoning about the current state and what to do next.
  Be specific about what information gaps exist.
  
action:
  type: <web_search|read_content|synthesize|finish>
  parameters:
    <action-specific parameters>
```"""
    
    def _default_research_goals(self) -> List[str]:
        """Return default research goals if none specified."""
        return [
            "Company culture and values",
            "Technology stack and engineering practices",
            "Recent news and developments",
            "Team structure and work environment",
            "Growth trajectory and market position"
        ]


# Company Research Tool Nodes

class WebSearchNode(Node):
    """
    Executes web searches using browser automation.
    
    This node wraps the web_search utility to perform searches based on
    queries from DecideActionNode and stores results in shared store.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Extract search parameters from shared store."""
        action_params = shared.get("action_params", {})
        query = action_params.get("query", "")
        
        if not query:
            raise ValueError("No search query provided")
        
        return {
            "query": query,
            "max_results": action_params.get("max_results", 10)
        }
    
    def exec(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute web search using utility."""
        from utils.web_search import WebSearcher
        
        try:
            # Run async search synchronously
            import asyncio
            
            async def _search():
                async with WebSearcher() as searcher:
                    results = await searcher.search(
                        params["query"], 
                        max_results=params["max_results"]
                    )
                    return [r.to_dict() for r in results]
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(_search())
            loop.close()
            
            return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: List[Dict[str, Any]]) -> str:
        """Store search results in shared store."""
        shared["search_results"] = exec_res
        
        # Update research state with found URLs
        if "research_state" not in shared:
            shared["research_state"] = {"information_gathered": {}}
        
        if "search_results" not in shared["research_state"]["information_gathered"]:
            shared["research_state"]["information_gathered"]["search_results"] = []
        
        # Add new results to gathered information
        for result in exec_res:
            shared["research_state"]["information_gathered"]["search_results"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")
            })
        
        logger.info(f"Found {len(exec_res)} search results")
        return "decide"  # Return to DecideActionNode


class ReadContentNode(Node):
    """
    Reads and extracts content from URLs.
    
    This node wraps the web_scraper utility to extract content from
    URLs identified by web searches or provided by DecideActionNode.
    """
    
    def __init__(self):
        super().__init__(max_retries=3, wait=2)
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Extract URL and focus parameters from shared store."""
        action_params = shared.get("action_params", {})
        url = action_params.get("url", "")
        
        if not url:
            raise ValueError("No URL provided to read")
        
        return {
            "url": url,
            "focus": action_params.get("focus", "")
        }
    
    def exec(self, params: Dict[str, Any]) -> Optional[str]:
        """Scrape content from URL using utility."""
        from utils.web_scraper import scrape_url
        
        try:
            content = scrape_url(params["url"])
            
            if content and params.get("focus"):
                # If focus area specified, we could filter content
                # For now, just log it
                logger.info(f"Reading content with focus on: {params['focus']}")
            
            return content
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return None
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Optional[str]) -> str:
        """Store scraped content in shared store."""
        shared["current_content"] = exec_res
        shared["current_url"] = prep_res["url"]
        
        if exec_res:
            # Update research state to indicate we have content to analyze
            if "research_state" not in shared:
                shared["research_state"] = {"information_gathered": {}}
            
            if "content_to_analyze" not in shared["research_state"]["information_gathered"]:
                shared["research_state"]["information_gathered"]["content_to_analyze"] = []
            
            shared["research_state"]["information_gathered"]["content_to_analyze"].append({
                "url": prep_res["url"],
                "has_content": True,
                "focus": prep_res.get("focus", "")
            })
            
            logger.info(f"Successfully read content from {prep_res['url']}")
        else:
            logger.warning(f"Failed to extract content from {prep_res['url']}")
        
        return "decide"  # Return to DecideActionNode


class SynthesizeInfoNode(Node):
    """
    Synthesizes gathered information into structured insights.
    
    This node uses an LLM to extract and organize specific information
    from the content gathered during research, based on research goals.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all research data for synthesis."""
        research_state = shared.get("research_state", {})
        information_gathered = research_state.get("information_gathered", {})
        
        # Collect all content to synthesize
        content_pieces = []
        
        # Add search results
        for result in information_gathered.get("search_results", []):
            content_pieces.append(f"Search Result: {result.get('title', '')}\n{result.get('snippet', '')}")
        
        # Add current content if available
        if shared.get("current_content"):
            content_pieces.append(f"Page Content:\n{shared['current_content'][:2000]}...")  # Limit length
        
        if not content_pieces:
            raise ValueError("No content available to synthesize")
        
        return {
            "content": "\n\n---\n\n".join(content_pieces),
            "company_name": shared.get("company_name", ""),
            "job_title": shared.get("job_title", ""),
            "research_goals": shared.get("research_goals", [])
        }
    
    def exec(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to synthesize information based on research goals."""
        prompt = f"""Analyze the following research content about {context['company_name']} and extract key insights.

Job Title: {context['job_title'] or 'Not specified'}

Research Goals:
{chr(10).join(f'- {goal}' for goal in context['research_goals'])}

Content to Analyze:
{context['content']}

Extract and organize insights into these categories:
1. Company Culture & Values
2. Technology Stack & Practices  
3. Recent Developments
4. Team & Work Environment
5. Market Position & Growth
6. Other Notable Information

For each category, provide 2-5 bullet points of specific, factual information found in the content.
If a category has no relevant information, mark it as "No information found."

Respond in YAML format with the structure shown above."""

        try:
            response = self.llm.call_llm_structured_sync(
                prompt=prompt,
                output_format="yaml",
                model="claude-3-opus"
            )
            
            return response
        except Exception as e:
            logger.error(f"Failed to synthesize information: {e}")
            # Return basic structure on error
            return {
                "company_culture_values": ["No information synthesized"],
                "technology_stack_practices": ["No information synthesized"],
                "recent_developments": ["No information synthesized"],
                "team_work_environment": ["No information synthesized"],
                "market_position_growth": ["No information synthesized"],
                "other_notable": ["Synthesis failed"]
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict[str, Any]) -> str:
        """Store synthesized insights in shared store."""
        # Initialize company research if not present
        if "company_research" not in shared:
            shared["company_research"] = {}
        
        # Update with synthesized information
        shared["company_research"].update(exec_res)
        
        # Mark synthesis as complete in research state
        if "research_state" in shared:
            shared["research_state"]["synthesis_complete"] = True
            
            # Store synthesized categories in information_gathered
            for category, items in exec_res.items():
                if isinstance(items, list) and items:
                    shared["research_state"]["information_gathered"][category] = items
        
        logger.info("Successfully synthesized research information")
        return "decide"  # Return to DecideActionNode for next decision


class ExperiencePrioritizationNode(Node):
    """
    Scores and ranks career experiences using weighted criteria.
    
    This is a pure Python node (no LLM) that implements deterministic scoring:
    - Relevance to role: 40%
    - Recency: 20%
    - Impact: 20%
    - Uniqueness: 10%
    - Growth demonstration: 10%
    """
    
    # Scoring weights
    WEIGHTS = {
        "relevance": 0.40,
        "recency": 0.20,
        "impact": 0.20,
        "uniqueness": 0.10,
        "growth": 0.10
    }
    
    def __init__(self):
        super().__init__(max_retries=1, wait=0)  # No retries needed for deterministic logic
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Extract career database and job requirements."""
        career_db = shared.get("career_db", {})
        requirements = shared.get("requirements", {})
        
        # Get all experiences to score
        experiences = []
        
        # Add professional experiences
        for exp in career_db.get("professional_experience", []):
            experiences.append({
                "type": "professional",
                "data": exp,
                "source": "professional_experience"
            })
        
        # Add projects
        for proj in career_db.get("projects", []):
            experiences.append({
                "type": "project",
                "data": proj,
                "source": "projects"
            })
        
        # Add other relevant experiences
        for edu in career_db.get("education", []):
            if edu.get("achievements") or edu.get("projects"):
                experiences.append({
                    "type": "education",
                    "data": edu,
                    "source": "education"
                })
        
        return {
            "experiences": experiences,
            "requirements": requirements,
            "current_date": shared.get("current_date", "2024-01-01")
        }
    
    def exec(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Score each experience and sort by composite score."""
        experiences = context["experiences"]
        requirements = context["requirements"]
        current_date = context["current_date"]
        
        scored_experiences = []
        
        for exp in experiences:
            scores = {
                "relevance": self._score_relevance(exp["data"], requirements),
                "recency": self._score_recency(exp["data"], current_date),
                "impact": self._score_impact(exp["data"]),
                "uniqueness": self._score_uniqueness(exp["data"], experiences),
                "growth": self._score_growth(exp["data"])
            }
            
            # Calculate weighted composite score
            composite_score = sum(
                scores[criterion] * self.WEIGHTS[criterion]
                for criterion in self.WEIGHTS
            )
            
            scored_experiences.append({
                "experience": exp,
                "scores": scores,
                "composite_score": composite_score
            })
        
        # Sort by composite score (highest first)
        scored_experiences.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return {"scored_experiences": scored_experiences}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> str:
        """Save prioritized experiences to shared store."""
        scored_experiences = exec_res["scored_experiences"]
        
        # Create prioritized list
        prioritized = []
        for i, scored_exp in enumerate(scored_experiences):
            exp_data = scored_exp["experience"]["data"]
            
            # Extract title/name
            title = (exp_data.get("role") or 
                    exp_data.get("title") or 
                    exp_data.get("name") or 
                    exp_data.get("degree", "Unknown"))
            
            prioritized.append({
                "rank": i + 1,
                "title": title,
                "type": scored_exp["experience"]["type"],
                "composite_score": round(scored_exp["composite_score"], 2),
                "scores": scored_exp["scores"],
                "data": exp_data
            })
        
        shared["prioritized_experiences"] = prioritized
        
        # Log top experiences
        logger.info(f"Prioritized {len(prioritized)} experiences")
        for exp in prioritized[:5]:
            logger.info(f"  #{exp['rank']}: {exp['title']} (score: {exp['composite_score']})")
        
        return "prioritize"
    
    def _score_relevance(self, experience: Dict[str, Any], requirements: Dict[str, Any]) -> float:
        """Score relevance to job requirements (0-100)."""
        if not requirements:
            return 50  # Default if no requirements
        
        score = 0
        max_score = 0
        
        # Get all required and preferred skills
        all_skills = []
        all_skills.extend(requirements.get("required_skills", []))
        all_skills.extend(requirements.get("preferred_skills", []))
        
        # Also consider technologies mentioned
        all_skills.extend(requirements.get("technologies", []))
        
        # Normalize skills for matching
        normalized_skills = [skill.lower() for skill in all_skills]
        
        # Check experience text for skill matches
        exp_text = self._get_experience_text(experience).lower()
        
        for skill in normalized_skills:
            max_score += 1
            if skill in exp_text:
                score += 1
        
        # Check for industry/domain match
        if requirements.get("industry"):
            max_score += 2  # Industry match is important
            if requirements["industry"].lower() in exp_text:
                score += 2
        
        return (score / max_score * 100) if max_score > 0 else 0
    
    def _score_recency(self, experience: Dict[str, Any], current_date: str) -> float:
        """Score based on recency (0-100)."""
        # Extract end date or use start date if ongoing
        end_date = experience.get("end_date") or experience.get("date") or current_date
        
        if end_date == "Present":
            return 100  # Current experience gets max score
        
        try:
            # Simple year extraction
            current_year = int(current_date.split("-")[0])
            exp_year = int(end_date.split("-")[0])
            
            years_ago = current_year - exp_year
            
            # Scoring: 100 for current, -10 per year, min 0
            return max(0, 100 - (years_ago * 10))
        except:
            return 50  # Default for unparseable dates
    
    def _score_impact(self, experience: Dict[str, Any]) -> float:
        """Score based on quantified impact (0-100)."""
        impact_keywords = [
            "increased", "decreased", "improved", "reduced", "saved",
            "generated", "achieved", "delivered", "launched", "built",
            "%", "$", "million", "thousand", "x"
        ]
        
        exp_text = self._get_experience_text(experience).lower()
        
        # Count impact indicators
        impact_count = sum(1 for keyword in impact_keywords if keyword in exp_text)
        
        # Check for specific quantified achievements
        achievements = experience.get("achievements", [])
        quantified_count = sum(
            1 for ach in achievements 
            if any(char.isdigit() for char in str(ach))
        )
        
        # Combined score
        total_indicators = impact_count + (quantified_count * 2)  # Weight quantified higher
        
        # Scale to 0-100 (5+ indicators = 100)
        return min(100, total_indicators * 20)
    
    def _score_uniqueness(self, experience: Dict[str, Any], all_experiences: List[Dict]) -> float:
        """Score based on uniqueness compared to other experiences (0-100)."""
        exp_text = self._get_experience_text(experience).lower()
        
        # Extract key terms (simple approach)
        exp_terms = set(word for word in exp_text.split() if len(word) > 4)
        
        # Compare with other experiences
        similarity_scores = []
        for other in all_experiences:
            if other["data"] == experience:  # Skip self
                continue
            
            other_text = self._get_experience_text(other["data"]).lower()
            other_terms = set(word for word in other_text.split() if len(word) > 4)
            
            # Jaccard similarity
            if exp_terms or other_terms:
                similarity = len(exp_terms & other_terms) / len(exp_terms | other_terms)
                similarity_scores.append(similarity)
        
        if not similarity_scores:
            return 100  # Unique by default
        
        # Average similarity
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        
        # Convert to uniqueness score (inverse of similarity)
        return int((1 - avg_similarity) * 100)
    
    def _score_growth(self, experience: Dict[str, Any]) -> float:
        """Score based on growth demonstration (0-100)."""
        growth_indicators = [
            "promoted", "advanced", "led", "managed", "grew",
            "expanded", "senior", "principal", "director", "head",
            "team", "department", "initiative", "transformation"
        ]
        
        exp_text = self._get_experience_text(experience).lower()
        
        # Count growth indicators
        growth_count = sum(1 for indicator in growth_indicators if indicator in exp_text)
        
        # Check for team size mentions
        import re
        team_patterns = [
            r'\d+\s*(?:person|people|member|engineer|developer)',
            r'team of \d+',
            r'\d+\+?\s*direct reports'
        ]
        
        team_mentions = sum(1 for pattern in team_patterns if re.search(pattern, exp_text))
        
        # Combined score
        total_indicators = growth_count + (team_mentions * 2)  # Weight team leadership
        
        # Scale to 0-100 (5+ indicators = 100)
        return min(100, total_indicators * 20)
    
    def _get_experience_text(self, experience: Dict[str, Any]) -> str:
        """Extract all text from an experience entry."""
        text_parts = []
        
        # Add all string fields
        for key, value in experience.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        text_parts.append(self._get_experience_text(item))
        
        return " ".join(text_parts)


class NarrativeStrategyNode(Node):
    """
    Synthesizes a complete narrative strategy for job applications.
    
    This LLM-driven node acts as an expert career coach, taking prioritized
    experiences and suitability assessment to craft a compelling narrative
    including must-tell experiences, differentiators, career arc, key messages,
    and detailed evidence stories in CAR format.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Gather prioritized experiences and suitability assessment."""
        prioritized_experiences = shared.get("prioritized_experiences", [])
        suitability_assessment = shared.get("suitability_assessment", {})
        requirements = shared.get("requirements", {})
        
        if not prioritized_experiences:
            raise ValueError("No prioritized experiences found for narrative strategy")
        
        if not suitability_assessment:
            raise ValueError("No suitability assessment found for narrative strategy")
        
        # Get job details
        job_title = shared.get("job_title", "")
        company_name = shared.get("company_name", "")
        
        return {
            "prioritized_experiences": prioritized_experiences,
            "suitability_assessment": suitability_assessment,
            "requirements": requirements,
            "job_title": job_title,
            "company_name": company_name
        }
    
    def exec(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate narrative strategy using LLM."""
        prompt = self._build_narrative_prompt(context)
        
        try:
            narrative_strategy = self.llm.call_llm_structured_sync(
                prompt=prompt,
                yaml_format=True,
                model="claude-3-opus"
            )
            
            # Validate narrative structure
            required_fields = [
                "must_tell_experiences",
                "differentiators", 
                "career_arc",
                "key_messages",
                "evidence_stories"
            ]
            
            for field in required_fields:
                if field not in narrative_strategy:
                    logger.warning(f"Missing required field in narrative strategy: {field}")
                    if field == "must_tell_experiences":
                        # Default to top 3 experiences
                        narrative_strategy[field] = [
                            self._summarize_experience(exp)
                            for exp in context["prioritized_experiences"][:3]
                        ]
                    elif field == "differentiators":
                        # Extract from suitability assessment
                        narrative_strategy[field] = context["suitability_assessment"].get(
                            "unique_value_proposition", "Strong technical background"
                        ).split(".")[:2]
                    elif field == "career_arc":
                        narrative_strategy[field] = {
                            "past": "Built strong technical foundation",
                            "present": "Leading complex projects",
                            "future": f"Ready to excel as {context['job_title']}"
                        }
                    elif field == "key_messages":
                        narrative_strategy[field] = [
                            "Strong technical skills match requirements",
                            "Proven track record of delivery",
                            "Ready to contribute immediately"
                        ]
                    elif field == "evidence_stories":
                        narrative_strategy[field] = []
            
            return narrative_strategy
            
        except Exception as e:
            logger.error(f"Failed to generate narrative strategy: {e}")
            # Return minimal strategy on error
            return self._create_fallback_strategy(context)
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict[str, Any]) -> str:
        """Store narrative strategy in shared store."""
        shared["narrative_strategy"] = exec_res
        
        logger.info("Narrative strategy complete:")
        logger.info(f"  Must-tell experiences: {len(exec_res.get('must_tell_experiences', []))}")
        logger.info(f"  Differentiators: {len(exec_res.get('differentiators', []))}")
        logger.info(f"  Key messages: {len(exec_res.get('key_messages', []))}")
        logger.info(f"  Evidence stories: {len(exec_res.get('evidence_stories', []))}")
        
        return "narrative"
    
    def _build_narrative_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for narrative strategy generation."""
        # Get top 5 experiences for context
        top_experiences = []
        for exp in context["prioritized_experiences"][:5]:
            top_experiences.append({
                "title": exp["title"],
                "score": exp["composite_score"],
                "relevance": exp["scores"]["relevance"],
                "impact": exp["scores"]["impact"],
                "summary": self._summarize_experience_data(exp["data"])
            })
        
        return f"""You are an expert career coach and storytelling strategist helping craft a compelling job application narrative.

## Context
Position: {context['job_title']} at {context['company_name']}

## Suitability Assessment Summary
Technical Fit: {context['suitability_assessment'].get('technical_fit_score', 'N/A')}/100
Cultural Fit: {context['suitability_assessment'].get('cultural_fit_score', 'N/A')}/100
Key Strengths: {', '.join(context['suitability_assessment'].get('key_strengths', [])[:3])}
Unique Value: {context['suitability_assessment'].get('unique_value_proposition', 'N/A')[:200]}...

## Top Prioritized Experiences
{self._format_top_experiences(top_experiences)}

## Your Task
Create a comprehensive narrative strategy that tells a compelling career story. Focus on:

1. **Must-Tell Experiences**: Select 2-3 experiences that MUST be highlighted
   - Choose highest impact + relevance combinations
   - Ensure they demonstrate required skills
   - Show progression and growth

2. **Differentiators**: Identify 1-2 unique experiences or combinations
   - What makes this candidate special?
   - Rare skill intersections
   - Unique perspectives or achievements

3. **Career Arc**: Craft the overall story (past → present → future)
   - Where they started and foundational skills
   - Current expertise and leadership
   - Future potential in this role

4. **Key Messages**: Define 3 concise messages to reinforce throughout
   - Core value propositions
   - Address any concerns proactively
   - Align with company needs

5. **Evidence Stories**: Create 1-2 detailed CAR format stories
   - Challenge: Specific situation and stakes
   - Action: What they did (skills demonstrated)
   - Result: Quantified impact and learning

Respond in YAML format:
```yaml
must_tell_experiences:
  - title: <Experience title>
    reason: <Why this is must-tell>
    key_points:
      - <Specific achievement or skill demonstration>
      - <Another key point>
  # 2-3 total experiences

differentiators:
  - <Unique aspect that sets them apart>
  - <Another differentiator>

career_arc:
  past: <Foundation and early growth>
  present: <Current expertise and leadership>
  future: <Vision for role and contribution>

key_messages:
  - <Concise value proposition>
  - <Address concern or highlight strength>
  - <Alignment with company needs>

evidence_stories:
  - title: <Story title>
    challenge: |
      <Detailed situation description including context,
       stakes, and why it was challenging>
    action: |
      <Specific actions taken, skills used, approach,
       collaboration, innovation demonstrated>
    result: |
      <Quantified outcomes, impact, recognition,
       learning, and lasting changes>
    skills_demonstrated:
      - <Skill 1>
      - <Skill 2>
  # 1-2 stories total
```"""
    
    def _format_top_experiences(self, experiences: List[Dict]) -> str:
        """Format top experiences for prompt."""
        formatted = []
        for i, exp in enumerate(experiences, 1):
            formatted.append(
                f"{i}. {exp['title']} (Score: {exp['score']:.1f}, "
                f"Relevance: {exp['relevance']:.0f}%, Impact: {exp['impact']:.0f}%)"
                f"\n   {exp['summary'][:150]}..."
            )
        return "\n".join(formatted)
    
    def _summarize_experience_data(self, exp_data: Dict[str, Any]) -> str:
        """Create brief summary of experience."""
        parts = []
        
        if "company" in exp_data:
            parts.append(f"at {exp_data['company']}")
        
        if "achievements" in exp_data and exp_data["achievements"]:
            parts.append(f"Key: {exp_data['achievements'][0]}")
        elif "description" in exp_data:
            parts.append(exp_data["description"][:100])
        
        if "technologies" in exp_data and exp_data["technologies"]:
            parts.append(f"Tech: {', '.join(exp_data['technologies'][:3])}")
        
        return " | ".join(parts)
    
    def _summarize_experience(self, exp: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a prioritized experience for fallback."""
        return {
            "title": exp["title"],
            "reason": f"High relevance ({exp['scores']['relevance']:.0f}%) and impact",
            "key_points": [
                "Demonstrates required skills",
                "Shows significant impact"
            ]
        }
    
    def _create_fallback_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal narrative strategy as fallback."""
        top_exps = context["prioritized_experiences"][:3]
        
        return {
            "must_tell_experiences": [
                self._summarize_experience(exp) for exp in top_exps
            ],
            "differentiators": [
                "Strong technical background",
                "Proven delivery track record"
            ],
            "career_arc": {
                "past": "Built strong technical foundation",
                "present": "Leading complex technical projects",
                "future": f"Ready to excel as {context['job_title']}"
            },
            "key_messages": [
                "Technical skills align with requirements",
                "Demonstrated impact in similar roles",
                "Cultural fit with company values"
            ],
            "evidence_stories": []
        }


class SuitabilityScoringNode(Node):
    """
    Performs holistic evaluation of job fit from a hiring manager perspective.
    
    This node takes requirement mappings, gaps, and company research to produce
    a comprehensive assessment including technical fit score, cultural fit score,
    key strengths, critical gaps, and unique value proposition.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all inputs needed for suitability assessment."""
        # Get requirement mapping data
        requirement_mapping = shared.get("requirement_mapping_final", {})
        gaps = shared.get("gaps", [])
        
        # Get company research data
        company_research = shared.get("company_research", {})
        
        # Get original requirements
        requirements = shared.get("requirements", {})
        
        # Get job details
        job_title = shared.get("job_title", "")
        company_name = shared.get("company_name", "")
        
        if not requirement_mapping:
            raise ValueError("No requirement mapping found for assessment")
        
        return {
            "requirement_mapping": requirement_mapping,
            "gaps": gaps,
            "company_research": company_research,
            "requirements": requirements,
            "job_title": job_title,
            "company_name": company_name
        }
    
    def exec(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive suitability assessment using LLM."""
        # First calculate technical fit score
        technical_fit_score = self._calculate_technical_fit(
            context["requirement_mapping"],
            context["requirements"]
        )
        
        # Prepare comprehensive prompt for LLM assessment
        prompt = self._build_assessment_prompt(context, technical_fit_score)
        
        try:
            # Get LLM assessment
            assessment = self.llm.call_llm_structured_sync(
                prompt=prompt,
                output_format="yaml",
                model="claude-3-opus"
            )
            
            # Ensure technical fit score is included
            assessment["technical_fit_score"] = technical_fit_score
            
            # Validate assessment structure
            required_fields = [
                "technical_fit_score",
                "cultural_fit_score", 
                "key_strengths",
                "critical_gaps",
                "unique_value_proposition",
                "overall_recommendation"
            ]
            
            for field in required_fields:
                if field not in assessment:
                    logger.warning(f"Missing required field in assessment: {field}")
                    if field == "cultural_fit_score":
                        assessment[field] = 70  # Default medium score
                    elif field in ["key_strengths", "critical_gaps"]:
                        assessment[field] = []
                    else:
                        assessment[field] = "Unable to assess"
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to generate suitability assessment: {e}")
            # Return minimal assessment on error
            return {
                "technical_fit_score": technical_fit_score,
                "cultural_fit_score": 50,
                "key_strengths": ["Technical skills match requirements"],
                "critical_gaps": ["Unable to perform full assessment"],
                "unique_value_proposition": "Candidate shows potential",
                "overall_recommendation": "Requires further evaluation"
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict[str, Any]) -> str:
        """Store suitability assessment in shared store."""
        shared["suitability_assessment"] = exec_res
        
        logger.info(f"Suitability assessment complete:")
        logger.info(f"  Technical fit: {exec_res['technical_fit_score']}/100")
        logger.info(f"  Cultural fit: {exec_res['cultural_fit_score']}/100")
        logger.info(f"  Strengths identified: {len(exec_res.get('key_strengths', []))}")
        logger.info(f"  Gaps identified: {len(exec_res.get('critical_gaps', []))}")
        
        return "default"
    
    def _calculate_technical_fit(self, mapping: Dict[str, Any], requirements: Dict[str, Any]) -> int:
        """
        Calculate technical fit score based on requirement coverage.
        
        Scoring logic:
        - Required skills: 60% of total score
        - Preferred skills: 20% of total score
        - Experience/Education: 20% of total score
        
        Each category scored by:
        - HIGH strength: 100% of points
        - MEDIUM strength: 60% of points
        - LOW strength: 30% of points
        - Missing: 0% of points
        """
        score = 0
        max_score = 100
        
        # Score required skills (60 points max)
        if "required_skills" in requirements and "required_skills" in mapping:
            required_score = self._score_category(
                requirements["required_skills"],
                mapping["required_skills"],
                60
            )
            score += required_score
        
        # Score preferred skills (20 points max)
        if "preferred_skills" in requirements and "preferred_skills" in mapping:
            preferred_score = self._score_category(
                requirements["preferred_skills"],
                mapping["preferred_skills"],
                20
            )
            score += preferred_score
        
        # Score experience/education (20 points max)
        other_score = 0
        other_max = 20
        other_categories = ["experience_years", "education", "certifications"]
        
        for category in other_categories:
            if category in requirements and category in mapping:
                cat_mapping = mapping[category]
                if isinstance(cat_mapping, dict) and not cat_mapping.get("is_gap", True):
                    strength = cat_mapping.get("strength_summary", "NONE")
                    if strength == "HIGH":
                        other_score += other_max / len(other_categories)
                    elif strength == "MEDIUM":
                        other_score += (other_max / len(other_categories)) * 0.6
                    elif strength == "LOW":
                        other_score += (other_max / len(other_categories)) * 0.3
        
        score += other_score
        
        # Ensure score is within bounds
        return max(0, min(100, int(score)))
    
    def _score_category(self, requirements: List[str], mappings: Dict[str, Any], max_points: int) -> float:
        """Score a category of requirements based on mapping strength."""
        if not requirements:
            return max_points  # No requirements means full credit
        
        total_score = 0
        points_per_req = max_points / len(requirements)
        
        for req in requirements:
            if req in mappings:
                req_data = mappings[req]
                if isinstance(req_data, dict):
                    strength = req_data.get("strength_summary", "NONE")
                    is_gap = req_data.get("is_gap", False)
                    
                    if not is_gap:
                        if strength == "HIGH":
                            total_score += points_per_req
                        elif strength == "MEDIUM":
                            total_score += points_per_req * 0.6
                        elif strength == "LOW":
                            total_score += points_per_req * 0.3
        
        return total_score
    
    def _build_assessment_prompt(self, context: Dict[str, Any], technical_score: int) -> str:
        """Build comprehensive assessment prompt for LLM."""
        return f"""You are a senior hiring manager evaluating a candidate for the position of {context['job_title']} at {context['company_name']}.

## Technical Fit Analysis
The candidate has achieved a technical fit score of {technical_score}/100 based on requirement coverage.

Requirement Mapping Summary:
{self._summarize_mapping(context['requirement_mapping'])}

Critical Gaps Identified:
{self._summarize_gaps(context['gaps'])}

## Company Context
{self._summarize_company_research(context['company_research'])}

## Your Task
Provide a comprehensive suitability assessment from a hiring manager's perspective. Consider both the quantitative technical fit and qualitative factors like cultural alignment and growth potential.

Focus on:
1. Cultural fit based on company values and work environment
2. Key strengths that make this candidate compelling
3. Critical gaps that need addressing
4. Unique value proposition - what rare combination of skills/experience makes them special
5. Overall hiring recommendation

Respond in YAML format:

```yaml
cultural_fit_score: <0-100>  # Based on alignment with company culture/values
key_strengths:
  - <Specific compelling strength with evidence>
  - <Another key differentiator>
  - <Continue for 3-5 total strengths>
critical_gaps:
  - <Most important gap with impact>
  - <Other significant gaps>
  - <Be honest but constructive>
unique_value_proposition: |
  <1-2 paragraphs describing the rare intersection of skills, experience, and perspective
   that makes this candidate uniquely valuable. Focus on combinations that are hard to find.>
overall_recommendation: |
  <1 paragraph with your hiring recommendation and reasoning. Be decisive but balanced.>
```"""
    
    def _summarize_mapping(self, mapping: Dict[str, Any]) -> str:
        """Summarize requirement mapping for prompt."""
        summary = []
        for category, items in mapping.items():
            if isinstance(items, dict):
                high_count = sum(1 for req, data in items.items() 
                               if isinstance(data, dict) and data.get("strength_summary") == "HIGH")
                medium_count = sum(1 for req, data in items.items() 
                                 if isinstance(data, dict) and data.get("strength_summary") == "MEDIUM")
                total = len(items)
                summary.append(f"- {category}: {high_count} HIGH, {medium_count} MEDIUM out of {total}")
        
        return "\n".join(summary) if summary else "No mapping data available"
    
    def _summarize_gaps(self, gaps: List[Dict[str, Any]]) -> str:
        """Summarize gaps for prompt."""
        if not gaps:
            return "No critical gaps identified"
        
        summary = []
        for gap in gaps[:5]:  # Top 5 gaps
            req = gap.get("requirement", "Unknown")
            gap_type = gap.get("gap_type", "missing")
            strategy = gap.get("mitigation_strategy", "")
            
            summary.append(f"- {req} ({gap_type})")
            if strategy:
                summary.append(f"  Mitigation: {strategy}")
        
        return "\n".join(summary)
    
    def _summarize_company_research(self, research: Dict[str, Any]) -> str:
        """Summarize company research for cultural fit assessment."""
        if not research:
            return "No company research available"
        
        sections = []
        
        if research.get("culture"):
            sections.append(f"Culture: {', '.join(research['culture'][:3])}")
        
        if research.get("technology_stack_practices"):
            sections.append(f"Tech Stack: {', '.join(research['technology_stack_practices'][:3])}")
            
        if research.get("team_work_environment"):
            sections.append(f"Work Environment: {', '.join(research['team_work_environment'][:3])}")
        
        return "\n".join(sections) if sections else "Limited company information available"


class CVGenerationNode(Node):
    """
    Generates a tailored CV in GitHub-flavored Markdown format.
    
    This LLM-driven node acts as a professional resume writer, using the
    narrative strategy to prioritize experiences and drawing detailed data
    from the career database. The CV emphasizes must-tell experiences while
    using job specification language for ATS optimization.
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Gather narrative strategy, career database, and requirements."""
        narrative_strategy = shared.get("narrative_strategy", {})
        career_db = shared.get("career_db", {})
        requirements = shared.get("requirements", {})
        job_title = shared.get("job_title", "")
        company_name = shared.get("company_name", "")
        
        # Check for empty dicts as well as missing
        if not narrative_strategy or narrative_strategy == {}:
            raise ValueError("No narrative strategy found for CV generation")
        
        if not career_db or career_db == {}:
            raise ValueError("No career database found for CV generation")
        
        return {
            "narrative_strategy": narrative_strategy,
            "career_db": career_db,
            "requirements": requirements,
            "job_title": job_title,
            "company_name": company_name
        }
    
    def exec(self, context: Dict[str, Any]) -> str:
        """Generate CV using professional resume writer prompt."""
        prompt = self._build_cv_prompt(context)
        
        try:
            cv_markdown = self.llm.call_llm_sync(
                prompt=prompt,
                max_tokens=3000
            )
            
            # Basic validation
            if not cv_markdown or len(cv_markdown) < 500:
                logger.warning("Generated CV seems too short, using fallback")
                return self._create_fallback_cv(context)
            
            return cv_markdown
            
        except Exception as e:
            logger.error(f"Failed to generate CV: {e}")
            return self._create_fallback_cv(context)
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: str) -> str:
        """Store generated CV in shared store."""
        shared["cv_markdown"] = exec_res
        
        # Log summary
        lines = exec_res.split('\n')
        logger.info(f"Generated CV with {len(lines)} lines")
        
        # Count key sections
        sections = [line for line in lines if line.startswith('##')]
        logger.info(f"CV sections: {len(sections)}")
        for section in sections[:5]:  # First 5 sections
            logger.info(f"  - {section.strip('#').strip()}")
        
        return "cv_generated"
    
    def _build_cv_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for CV generation."""
        narrative = context["narrative_strategy"]
        career_db = context["career_db"]
        requirements = context["requirements"]
        job_title = context["job_title"]
        company_name = context["company_name"]
        
        # Extract key information
        must_tell_titles = [exp["title"] for exp in narrative.get("must_tell_experiences", [])]
        key_messages = narrative.get("key_messages", [])
        differentiators = narrative.get("differentiators", [])
        career_arc = narrative.get("career_arc", {})
        
        # Get all skills from requirements
        all_skills = set()
        all_skills.update(requirements.get("required_skills", []))
        all_skills.update(requirements.get("preferred_skills", []))
        all_skills.update(requirements.get("technologies", []))
        
        return f"""You are an expert resume writer specializing in technical roles. Create a compelling CV for {job_title} at {company_name}.

NARRATIVE STRATEGY TO FOLLOW:

Key Messages to Emphasize:
{chr(10).join(f"- {msg}" for msg in key_messages)}

Must-Tell Experiences (feature prominently):
{chr(10).join(f"- {title}" for title in must_tell_titles)}

Differentiators:
{chr(10).join(f"- {diff}" for diff in differentiators)}

Career Arc:
- Past: {career_arc.get('past', 'N/A')}
- Present: {career_arc.get('present', 'N/A')}
- Future: {career_arc.get('future', 'N/A')}

TARGET JOB REQUIREMENTS:
{self._format_requirements(requirements)}

CAREER DATABASE:
{self._format_career_db_for_cv(career_db, must_tell_titles)}

INSTRUCTIONS:
1. Create a professional summary that weaves together all 3 key messages and highlights differentiators
2. Feature must-tell experiences prominently with expanded bullet points
3. Use job specification language throughout (mirror the requirements)
4. Include quantified achievements with specific metrics
5. Minimize or summarize experiences not in the must-tell list
6. Ensure all required skills from the job are represented
7. Use GitHub-flavored Markdown with proper formatting

OUTPUT FORMAT:
```markdown
# [Full Name]

## Professional Summary
[3-4 lines incorporating all key messages and differentiators]

## Core Skills
- **[Category]**: skill1, skill2, skill3
- **[Category]**: skill1, skill2, skill3

## Professional Experience

### [Job Title] | [Company] | [Date Range]
[Brief context if must-tell experience]
- [Achievement with metric using job spec language]
- [Achievement with metric using job spec language]
- [Achievement demonstrating required skill]

### [Earlier roles summarized if not must-tell]

## Education
### [Degree] | [Institution] | [Year]

## Certifications & Training
- [Relevant certifications]

## Projects [Optional if relevant]
### [Project Name]
[Brief description with technologies and impact]
```

Generate the CV now:"""
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements for prompt context."""
        sections = []
        
        if requirements.get("required_skills"):
            sections.append(f"Required Skills: {', '.join(requirements['required_skills'])}")
        
        if requirements.get("preferred_skills"):
            sections.append(f"Preferred Skills: {', '.join(requirements['preferred_skills'])}")
        
        if requirements.get("experience_years"):
            years = requirements["experience_years"]
            if isinstance(years, dict):
                sections.append(f"Experience: {years.get('min', 0)}-{years.get('max', 'N/A')} years")
            else:
                sections.append(f"Experience: {years} years")
        
        if requirements.get("education"):
            sections.append(f"Education: {', '.join(requirements['education'])}")
        
        return '\n'.join(sections) if sections else "No specific requirements provided"
    
    def _format_career_db_for_cv(self, career_db: Dict[str, Any], must_tell_titles: List[str]) -> str:
        """Format career database focusing on must-tell experiences."""
        sections = []
        
        # Personal info
        personal = career_db.get("personal_information", {})
        if personal:
            sections.append(f"Name: {personal.get('name', 'Not provided')}")
            sections.append(f"Email: {personal.get('email', 'Not provided')}")
            sections.append(f"Location: {personal.get('location', 'Not provided')}")
            sections.append("")
        
        # Professional experience (prioritize must-tell)
        experiences = career_db.get("professional_experience", [])
        if experiences:
            sections.append("PROFESSIONAL EXPERIENCE:")
            
            # First add must-tell experiences
            for exp in experiences:
                role_title = f"{exp.get('role', '')} at {exp.get('company', '')}"
                if any(title in role_title for title in must_tell_titles):
                    sections.append(f"\n[MUST-TELL] {role_title}")
                    sections.append(f"Dates: {exp.get('start_date', '')} - {exp.get('end_date', '')}")
                    
                    if exp.get("responsibilities"):
                        sections.append("Responsibilities:")
                        for resp in exp["responsibilities"][:3]:
                            sections.append(f"  - {resp}")
                    
                    if exp.get("achievements"):
                        sections.append("Achievements:")
                        for ach in exp["achievements"]:
                            sections.append(f"  - {ach}")
                    
                    if exp.get("technologies"):
                        sections.append(f"Technologies: {', '.join(exp['technologies'])}")
            
            # Then add other experiences briefly
            for exp in experiences:
                role_title = f"{exp.get('role', '')} at {exp.get('company', '')}"
                if not any(title in role_title for title in must_tell_titles):
                    sections.append(f"\n{role_title} ({exp.get('start_date', '')} - {exp.get('end_date', '')})")
                    if exp.get("achievements"):
                        sections.append(f"  Key: {exp['achievements'][0]}")
        
        # Education
        education = career_db.get("education", [])
        if education:
            sections.append("\nEDUCATION:")
            for edu in education:
                sections.append(f"- {edu.get('degree', '')} from {edu.get('institution', '')} ({edu.get('graduation_date', '')})")
        
        # Skills
        skills = career_db.get("skills", {})
        if skills:
            sections.append("\nSKILLS:")
            for category, skill_list in skills.items():
                if skill_list:
                    sections.append(f"- {category}: {', '.join(skill_list)}")
        
        # Certifications
        certs = career_db.get("certifications", [])
        if certs:
            sections.append("\nCERTIFICATIONS:")
            for cert in certs:
                sections.append(f"- {cert.get('name', '')} ({cert.get('date', '')})")
        
        return '\n'.join(sections)
    
    def _create_fallback_cv(self, context: Dict[str, Any]) -> str:
        """Create a basic CV if generation fails."""
        career_db = context["career_db"]
        narrative = context["narrative_strategy"]
        
        personal = career_db.get("personal_information", {})
        name = personal.get("name", "Professional")
        email = personal.get("email", "email@example.com")
        location = personal.get("location", "Location")
        
        # Build fallback CV
        cv_lines = [
            f"# {name}",
            f"{email} | {location}",
            "",
            "## Professional Summary"
        ]
        
        # Add key messages as summary
        for msg in narrative.get("key_messages", ["Experienced professional"]):
            cv_lines.append(f"- {msg}")
        
        cv_lines.extend(["", "## Professional Experience", ""])
        
        # Add experiences
        for exp in career_db.get("professional_experience", [])[:5]:
            cv_lines.append(f"### {exp.get('role', 'Role')} | {exp.get('company', 'Company')} | {exp.get('start_date', 'Start')} - {exp.get('end_date', 'End')}")
            
            # Add top achievements
            for ach in exp.get("achievements", [])[:3]:
                cv_lines.append(f"- {ach}")
            cv_lines.append("")
        
        # Add education
        cv_lines.extend(["## Education", ""])
        for edu in career_db.get("education", []):
            cv_lines.append(f"### {edu.get('degree', 'Degree')} | {edu.get('institution', 'Institution')} | {edu.get('graduation_date', 'Year')}")
            cv_lines.append("")
        
        # Add skills
        skills = career_db.get("skills", {})
        if skills:
            cv_lines.extend(["## Technical Skills", ""])
            for category, skill_list in skills.items():
                if skill_list:
                    cv_lines.append(f"- **{category}**: {', '.join(skill_list)}")
        
        return '\n'.join(cv_lines)


class CoverLetterNode(Node):
    """
    Generates a compelling cover letter following a 5-part structure.
    
    This LLM-driven node creates a personalized cover letter using:
    - Hook: Addresses company need/goal from research
    - Value Proposition: States unique value using differentiators
    - Evidence: Provides 2-3 CAR format stories
    - Company Fit: Demonstrates cultural alignment
    - Call to Action: Confident and specific next steps
    """
    
    def __init__(self):
        super().__init__(max_retries=2, wait=1)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all data needed for cover letter generation."""
        narrative_strategy = shared.get("narrative_strategy", {})
        company_research = shared.get("company_research", {})
        suitability_assessment = shared.get("suitability_assessment", {})
        requirements = shared.get("requirements", {})
        job_title = shared.get("job_title", "")
        company_name = shared.get("company_name", "")
        career_db = shared.get("career_db", {})
        
        # Validate required data
        if not narrative_strategy or narrative_strategy == {}:
            raise ValueError("No narrative strategy found for cover letter generation")
        
        if not company_research or company_research == {}:
            logger.warning("No company research available - cover letter will be generic")
            company_research = self._create_generic_company_research(company_name)
        
        if not suitability_assessment or suitability_assessment == {}:
            raise ValueError("No suitability assessment found for cover letter generation")
        
        return {
            "narrative_strategy": narrative_strategy,
            "company_research": company_research,
            "suitability_assessment": suitability_assessment,
            "requirements": requirements,
            "job_title": job_title,
            "company_name": company_name,
            "career_db": career_db
        }
    
    def exec(self, context: Dict[str, Any]) -> str:
        """Generate cover letter using professional writer prompt."""
        prompt = self._build_cover_letter_prompt(context)
        
        try:
            cover_letter = self.llm.call_llm_sync(
                prompt=prompt,
                max_tokens=2000
            )
            
            # Basic validation
            if not cover_letter or len(cover_letter) < 300:
                logger.warning("Generated cover letter seems too short, using fallback")
                return self._create_fallback_cover_letter(context)
            
            # Check for 5-part structure
            if not self._validate_structure(cover_letter):
                logger.warning("Cover letter missing required structure, using fallback")
                return self._create_fallback_cover_letter(context)
            
            return cover_letter
            
        except Exception as e:
            logger.error(f"Failed to generate cover letter: {e}")
            return self._create_fallback_cover_letter(context)
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: str) -> str:
        """Store generated cover letter in shared store."""
        shared["cover_letter_text"] = exec_res
        
        # Log summary
        word_count = len(exec_res.split())
        paragraph_count = len([p for p in exec_res.split('\n\n') if p.strip()])
        
        logger.info(f"Generated cover letter with {word_count} words in {paragraph_count} paragraphs")
        
        # Check for key elements
        elements = {
            "Hook": "Dear" in exec_res or "Hiring" in exec_res,
            "Company mention": shared.get("company_name", "") in exec_res,
            "Role mention": shared.get("job_title", "") in exec_res,
            "Call to action": any(phrase in exec_res.lower() for phrase in ["look forward", "excited to", "eager to"])
        }
        
        logger.info(f"Cover letter elements: {sum(elements.values())}/{len(elements)} present")
        
        return "cover_letter_generated"
    
    def _build_cover_letter_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for cover letter generation."""
        narrative = context["narrative_strategy"]
        company = context["company_research"]
        assessment = context["suitability_assessment"]
        job_title = context["job_title"]
        company_name = context["company_name"]
        career_db = context["career_db"]
        
        # Extract key elements
        career_arc = narrative.get("career_arc", {})
        key_messages = narrative.get("key_messages", [])
        must_tells = narrative.get("must_tell_experiences", [])
        differentiators = narrative.get("differentiators", [])
        evidence_stories = narrative.get("evidence_stories", [])
        
        # Get personal info
        personal = career_db.get("personal_information", {})
        name = personal.get("name", "Your Name")
        
        return f"""You are an expert cover letter writer creating a compelling letter for {job_title} at {company_name}.

NARRATIVE STRATEGY:
Career Arc:
- Present: {career_arc.get('present', 'Current role')}
- Future: {career_arc.get('future', 'Target role')}

Key Messages:
{chr(10).join(f"- {msg}" for msg in key_messages)}

Differentiators:
{chr(10).join(f"- {diff}" for diff in differentiators)}

Evidence Stories Available:
{self._format_evidence_stories(evidence_stories, must_tells)}

COMPANY RESEARCH:
{self._format_company_research(company)}

SUITABILITY ASSESSMENT:
Unique Value Proposition: {assessment.get('unique_value_proposition', 'Strong candidate')}
Technical Fit: {assessment.get('technical_fit_score', 'N/A')}/100
Cultural Fit: {assessment.get('cultural_fit_score', 'N/A')}/100
Key Strengths: {', '.join(assessment.get('key_strengths', ['Technical expertise'])[:3])}

COVER LETTER STRUCTURE (MUST FOLLOW):

1. HOOK (Opening Paragraph)
- Start with company's current need/goal from research
- Connect to your {career_arc.get('present', 'current expertise')}
- Mention {job_title} role and why you're writing
- Use first key message: {key_messages[0] if key_messages else 'Your expertise'}

2. VALUE PROPOSITION (Second Paragraph)
- State your unique value: "{assessment.get('unique_value_proposition', differentiators[0] if differentiators else 'Your unique value')}"
- Reference {must_tells[0]['title'] if must_tells else 'your most relevant experience'}
- Include specific metrics from that experience
- Connect to company's needs

3. EVIDENCE (Third Paragraph)
- Tell a CAR story that demonstrates required skills
- Use evidence story if available, otherwise expand on must-tell experience
- Show quantified impact
- Mirror job specification language

4. COMPANY FIT (Fourth Paragraph)
- Reference specific aspect of company culture: {company.get('culture', ['innovation'])[:1]}
- Connect to your future vision: {career_arc.get('future', 'career goals')}
- Show how your differentiator aligns with company values
- Demonstrate you've done research

5. CALL TO ACTION (Closing Paragraph)
- Reinforce all 3 key messages succinctly
- Express enthusiasm for contributing to {company_name}
- Confident request for interview
- Professional closing

TONE: Professional yet personable, confident without arrogance, specific not generic

Generate the cover letter now (use "Dear Hiring Manager" for salutation):"""
    
    def _format_evidence_stories(self, stories: List[Dict], must_tells: List[Dict]) -> str:
        """Format evidence stories for prompt context."""
        if stories:
            formatted = []
            for story in stories[:2]:  # Max 2 stories
                formatted.append(f"- {story.get('title', 'Story')}: {story.get('challenge', '')[:100]}...")
            return '\n'.join(formatted)
        elif must_tells:
            # Use must-tell experiences as backup
            formatted = []
            for exp in must_tells[:2]:
                points = exp.get('key_points', [])
                if points:
                    formatted.append(f"- {exp.get('title', 'Experience')}: {points[0]}")
            return '\n'.join(formatted) if formatted else "- Use experiences from career database"
        return "- Draw from career database experiences"
    
    def _format_company_research(self, research: Dict[str, Any]) -> str:
        """Format company research for prompt."""
        sections = []
        
        if research.get("mission"):
            sections.append(f"Mission: {research['mission'][:200]}")
        
        if research.get("culture"):
            sections.append(f"Culture: {', '.join(research['culture'][:3])}")
        
        if research.get("strategic_importance"):
            sections.append(f"Role Importance: {research['strategic_importance'][:200]}")
        
        if research.get("recent_developments"):
            sections.append(f"Recent: {', '.join(research['recent_developments'][:2])}")
        
        return '\n'.join(sections) if sections else "Limited company information available"
    
    def _validate_structure(self, cover_letter: str) -> bool:
        """Validate cover letter has required 5-part structure."""
        # Simple validation - check for reasonable paragraph count
        paragraphs = [p for p in cover_letter.split('\n\n') if p.strip()]
        
        # Should have at least 5 paragraphs (can have more with address/date)
        if len(paragraphs) < 5:
            return False
        
        # Check for key elements
        has_greeting = any(p.startswith(("Dear", "To", "Hello")) for p in paragraphs)
        has_closing = any(any(closing in p for closing in ["Sincerely", "Best regards", "Kind regards"]) for p in paragraphs[-2:])
        
        return has_greeting and has_closing
    
    def _create_generic_company_research(self, company_name: str) -> Dict[str, Any]:
        """Create generic company research when none available."""
        return {
            "mission": f"To be a leader in the industry",
            "culture": ["innovation", "collaboration", "excellence"],
            "strategic_importance": "This role is critical for the company's growth",
            "recent_developments": ["expanding operations", "investing in technology"]
        }
    
    def _create_fallback_cover_letter(self, context: Dict[str, Any]) -> str:
        """Create a basic cover letter if generation fails."""
        narrative = context["narrative_strategy"]
        assessment = context["suitability_assessment"]
        job_title = context["job_title"]
        company_name = context["company_name"]
        career_db = context["career_db"]
        
        personal = career_db.get("personal_information", {})
        name = personal.get("name", "Your Name")
        
        career_arc = narrative.get("career_arc", {})
        key_messages = narrative.get("key_messages", ["Strong technical skills", "Proven track record", "Ready to contribute"])
        differentiators = narrative.get("differentiators", ["Unique combination of skills"])
        must_tells = narrative.get("must_tell_experiences", [])
        
        # Build fallback letter
        letter_parts = [
            "Dear Hiring Manager,",
            "",
            # Hook
            f"As a {career_arc.get('present', 'experienced professional')}, I was excited to discover the {job_title} opportunity at {company_name}. {key_messages[0]}.",
            "",
            # Value Proposition
            f"I offer {assessment.get('unique_value_proposition', differentiators[0] if differentiators else 'strong technical expertise')}. "
            f"In my recent role {must_tells[0]['title'] if must_tells else 'in my current position'}, "
            f"I {must_tells[0]['key_points'][0] if must_tells and must_tells[0].get('key_points') else 'delivered significant results'}.",
            "",
            # Evidence
            f"Throughout my career, I have consistently {key_messages[1]}. "
            f"For example, {must_tells[1]['key_points'][0] if len(must_tells) > 1 and must_tells[1].get('key_points') else 'I have led successful projects'}. "
            f"This experience directly aligns with your requirements.",
            "",
            # Company Fit
            f"I am particularly drawn to {company_name}'s commitment to innovation and growth. "
            f"{career_arc.get('future', 'I am ready to bring my expertise to your team')}. "
            f"My {differentiators[0] if differentiators else 'unique background'} would add valuable perspective to your team.",
            "",
            # Call to Action
            f"I am confident that my combination of {key_messages[0] if len(key_messages) > 0 else 'technical expertise'}, "
            f"{key_messages[1] if len(key_messages) > 1 else 'proven leadership'}, "
            f"and {key_messages[2] if len(key_messages) > 2 else 'delivery excellence'} "
            f"makes me an ideal candidate for this role. I would welcome the opportunity to discuss how I can contribute to {company_name}'s continued success.",
            "",
            "Thank you for your consideration. I look forward to speaking with you soon.",
            "",
            "Sincerely,",
            name
        ]
        
        return '\n'.join(letter_parts)


class ScanDocumentsNode(Node):
    """Scans configured sources for work experience documents."""
    
    def prep(self, shared: dict) -> dict:
        """Read scan configuration from shared store."""
        return {
            "google_drive_folders": shared.get("scan_config", {}).get("google_drive_folders", []),
            "local_directories": shared.get("scan_config", {}).get("local_directories", []),
            "file_types": shared.get("scan_config", {}).get("file_types", [".pdf", ".docx", ".md"]),
            "date_filter": shared.get("scan_config", {}).get("date_filter", {})
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Execute document scanning across all configured sources."""
        from utils.document_scanner import scan_documents, DocumentMetadata
        from datetime import datetime
        
        # Prepare paths to scan
        paths_to_scan = []
        scanner_types = {}
        
        # Add Google Drive folders
        for folder in prep_res["google_drive_folders"]:
            folder_id = folder.get("folder_id")
            if folder_id:
                paths_to_scan.append(folder_id)
                scanner_types[folder_id] = 'google_drive'
        
        # Add local directories
        for directory in prep_res["local_directories"]:
            path = directory.get("path") if isinstance(directory, dict) else directory
            if path:
                # Expand user home directory
                path = os.path.expanduser(path)
                paths_to_scan.append(path)
                scanner_types[path] = 'local'
        
        # Parse date filter
        date_filter = prep_res["date_filter"]
        min_date = None
        max_date = None
        
        if date_filter.get("min_date"):
            try:
                min_date = datetime.fromisoformat(date_filter["min_date"])
            except:
                pass
        
        if date_filter.get("max_date"):
            try:
                max_date = datetime.fromisoformat(date_filter["max_date"])
            except:
                pass
        
        # Scan documents
        all_documents = []
        scan_errors = []
        
        for path in paths_to_scan:
            try:
                # Determine scanner type
                scanner_type = scanner_types.get(path, 'auto')
                
                # Scan this path
                documents = scan_documents(
                    paths=[path],
                    scanner_type=scanner_type,
                    file_types=set(prep_res["file_types"]),
                    min_date=min_date,
                    max_date=max_date
                )
                
                all_documents.extend(documents)
                
            except Exception as e:
                error_msg = f"Failed to scan {path}: {str(e)}"
                scan_errors.append({
                    "path": path,
                    "error": str(e),
                    "type": type(e).__name__
                })
                print(f"Warning: {error_msg}")
        
        # Convert documents to dict format
        document_dicts = [doc.to_dict() for doc in all_documents]
        
        return {
            "documents": document_dicts,
            "scan_errors": scan_errors,
            "total_found": len(document_dicts)
        }
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Store discovered documents in shared store."""
        # Store documents
        shared["document_sources"] = exec_res["documents"]
        
        # Store any errors
        if exec_res["scan_errors"]:
            shared["scan_errors"] = exec_res["scan_errors"]
        
        # Log summary
        print(f"Document scan complete: {exec_res['total_found']} documents found")
        if exec_res["scan_errors"]:
            print(f"Encountered {len(exec_res['scan_errors'])} errors during scanning")
        
        return "continue"


class ExtractExperienceNode(BatchNode):
    """Extracts work experience from parsed documents using LLM analysis."""
    
    def __init__(self):
        super().__init__()
        self.llm = get_default_llm_wrapper()
        self.batch_size = 5  # Process 5 documents at a time
    
    def prep(self, shared: dict) -> dict:
        """Prepare documents for processing."""
        documents = shared.get("document_sources", [])
        
        # Load career schema if available
        career_schema = None
        if "career_database_schema" in shared:
            career_schema = shared["career_database_schema"]
        else:
            # Use default schema structure
            career_schema = self._get_default_career_schema()
        
        return {
            "documents": documents,
            "batch_size": self.batch_size,
            "career_schema": career_schema,
            "extraction_mode": shared.get("extraction_mode", "comprehensive")
        }
    
    def exec_batch(self, batch: List[dict], prep_res: dict) -> List[dict]:
        """Process a batch of documents."""
        from utils.document_parser import parse_document
        import json
        
        extracted = []
        
        for doc in batch:
            try:
                # Parse document
                logger.info(f"Parsing document: {doc['name']}")
                parsed = parse_document(doc['path'], parser_type='auto')
                
                if parsed.error:
                    logger.error(f"Failed to parse {doc['name']}: {parsed.error}")
                    extracted.append({
                        "document_source": doc['path'],
                        "document_name": doc['name'],
                        "extraction_confidence": 0.0,
                        "error": parsed.error,
                        "experiences": []
                    })
                    continue
                
                # Extract experience via LLM
                logger.info(f"Extracting experience from {doc['name']}")
                experience_data = self._extract_experience(
                    parsed, 
                    doc,
                    prep_res["career_schema"],
                    prep_res["extraction_mode"]
                )
                
                extracted.append(experience_data)
                
            except Exception as e:
                logger.error(f"Error processing document {doc['name']}: {str(e)}")
                extracted.append({
                    "document_source": doc['path'],
                    "document_name": doc['name'],
                    "extraction_confidence": 0.0,
                    "error": str(e),
                    "experiences": []
                })
        
        return extracted
    
    def _extract_experience(self, parsed_doc, doc_metadata, career_schema, extraction_mode):
        """Extract experience from a single document using LLM."""
        # Determine document type
        doc_type = self._classify_document(parsed_doc, doc_metadata)
        
        # Create extraction prompt
        system_prompt = self._create_system_prompt(career_schema, doc_type, extraction_mode)
        user_prompt = self._create_user_prompt(parsed_doc, doc_metadata, doc_type)
        
        try:
            # Call LLM
            response = self.llm.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=4000
            )
            
            # Parse YAML response
            extracted_data = yaml.safe_load(response)
            
            # Validate and structure the response
            structured_data = self._structure_extraction(
                extracted_data, 
                doc_metadata,
                doc_type
            )
            
            return structured_data
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse LLM response as YAML: {e}")
            # Try to extract what we can
            return self._create_fallback_extraction(parsed_doc, doc_metadata, str(response))
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise
    
    def _classify_document(self, parsed_doc, doc_metadata):
        """Classify document type based on content and metadata."""
        content_lower = parsed_doc.content.lower()
        name_lower = doc_metadata['name'].lower()
        
        # Check for resume indicators
        if any(term in name_lower for term in ['resume', 'cv', 'curriculum']):
            return "resume"
        
        if any(term in content_lower[:500] for term in ['experience', 'education', 'skills', 'objective']):
            return "resume"
        
        # Check for portfolio/project indicators
        if any(term in name_lower for term in ['portfolio', 'project', 'case study']):
            return "portfolio"
        
        # Check for specific project document patterns
        if any(section.title.lower() in ['overview', 'background', 'implementation', 'results'] 
               for section in parsed_doc.sections):
            return "project"
        
        # Default
        return "general"
    
    def _create_system_prompt(self, career_schema, doc_type, extraction_mode):
        """Create system prompt for experience extraction."""
        schema_yaml = yaml.dump(career_schema, default_flow_style=False)
        
        base_prompt = f"""You are an expert career analyst extracting work experience from documents.
Your task is to extract structured information that matches this career database schema:

{schema_yaml}

Document Type: {doc_type}
Extraction Mode: {extraction_mode}

Focus on extracting:
1. Complete work history with accurate dates
2. Detailed project information nested within relevant work experiences
3. Technologies and skills used (be comprehensive)
4. Quantifiable achievements with specific metrics
5. Leadership and team experiences
6. Company culture insights where mentioned

Guidelines:
- Extract ALL work experiences found in the document
- For each experience, extract ALL nested projects mentioned
- Preserve exact dates and durations as written
- Capture metrics and numbers precisely
- Infer missing information only when strongly implied
- Use null for truly missing required fields
- Ensure technologies lists are comprehensive
- Link projects to their parent work experience

Return the extracted data as valid YAML matching the schema structure.
Only include the data, no explanations or comments."""
        
        if extraction_mode == "comprehensive":
            base_prompt += "\n\nBe extremely thorough - extract every detail available."
        elif extraction_mode == "targeted":
            base_prompt += "\n\nFocus on technical roles and achievements."
        
        return base_prompt
    
    def _create_user_prompt(self, parsed_doc, doc_metadata, doc_type):
        """Create user prompt with document content."""
        # Limit content length for very large documents
        content = parsed_doc.content
        if len(content) > 15000:
            content = content[:15000] + "\n\n[Content truncated...]"
        
        prompt = f"""Extract all work experience from this document:

Document Name: {doc_metadata['name']}
Document Type: {doc_type}
Source: {doc_metadata['source']}

Content:
{content}

Remember to:
1. Extract complete work history
2. Include all projects within each role
3. Capture all technologies mentioned
4. Preserve quantified achievements
5. Note team sizes and leadership roles

Return as structured YAML matching the career database schema."""
        
        return prompt
    
    def _structure_extraction(self, extracted_data, doc_metadata, doc_type):
        """Structure and validate extracted data."""
        # Initialize result structure
        result = {
            "document_source": doc_metadata['path'],
            "document_name": doc_metadata['name'],
            "document_type": doc_type,
            "extraction_confidence": 0.9,  # Default high confidence
            "personal_info": extracted_data.get("personal_info", {}),
            "experiences": [],
            "education": extracted_data.get("education", []),
            "skills": extracted_data.get("skills", {}),
            "projects": extracted_data.get("projects", []),
            "certifications": extracted_data.get("certifications", []),
            "publications": extracted_data.get("publications", []),
            "awards": extracted_data.get("awards", [])
        }
        
        # Process experiences
        for exp in extracted_data.get("experience", []):
            structured_exp = {
                "company": exp.get("company", ""),
                "title": exp.get("title", ""),
                "duration": exp.get("duration", ""),
                "location": exp.get("location", ""),
                "description": exp.get("description", ""),
                "achievements": exp.get("achievements", []),
                "technologies": exp.get("technologies", []),
                "team_size": exp.get("team_size"),
                "projects": []
            }
            
            # Process nested projects
            for proj in exp.get("projects", []):
                structured_proj = {
                    "title": proj.get("title", ""),
                    "description": proj.get("description", ""),
                    "achievements": proj.get("achievements", []),
                    "role": proj.get("role", ""),
                    "technologies": proj.get("technologies", []),
                    "key_stakeholders": proj.get("key_stakeholders", []),
                    "notable_challenges": proj.get("notable_challenges", [])
                }
                structured_exp["projects"].append(structured_proj)
            
            result["experiences"].append(structured_exp)
        
        # Calculate confidence based on completeness
        confidence = self._calculate_extraction_confidence(result)
        result["extraction_confidence"] = confidence
        
        return result
    
    def _calculate_extraction_confidence(self, extracted_data):
        """Calculate confidence score based on extraction completeness."""
        score = 0.0
        factors = 0
        
        # Check experiences
        if extracted_data["experiences"]:
            score += 0.3
            factors += 0.3
            
            # Check completeness of experiences
            complete_experiences = sum(
                1 for exp in extracted_data["experiences"]
                if exp.get("company") and exp.get("title") and exp.get("duration")
            )
            if complete_experiences > 0:
                score += 0.2 * (complete_experiences / len(extracted_data["experiences"]))
                factors += 0.2
        
        # Check education
        if extracted_data["education"]:
            score += 0.1
            factors += 0.1
        
        # Check skills
        if extracted_data["skills"] and extracted_data["skills"].get("technical"):
            score += 0.1
            factors += 0.1
        
        # Check for projects
        total_projects = len(extracted_data["projects"])
        for exp in extracted_data["experiences"]:
            total_projects += len(exp.get("projects", []))
        if total_projects > 0:
            score += 0.1
            factors += 0.1
        
        # Check personal info
        if extracted_data["personal_info"] and extracted_data["personal_info"].get("name"):
            score += 0.1
            factors += 0.1
        
        # Check for quantified achievements
        has_metrics = False
        for exp in extracted_data["experiences"]:
            for achievement in exp.get("achievements", []):
                if any(char.isdigit() for char in achievement):
                    has_metrics = True
                    break
        if has_metrics:
            score += 0.1
            factors += 0.1
        
        return round(score / factors if factors > 0 else 0.0, 2)
    
    def _create_fallback_extraction(self, parsed_doc, doc_metadata, raw_response):
        """Create a basic extraction when YAML parsing fails."""
        return {
            "document_source": doc_metadata['path'],
            "document_name": doc_metadata['name'],
            "extraction_confidence": 0.3,
            "error": "Failed to parse structured response",
            "raw_extraction": raw_response[:1000],  # First 1000 chars
            "experiences": [],
            "education": [],
            "skills": {},
            "projects": []
        }
    
    def _get_default_career_schema(self):
        """Get default career database schema structure."""
        return {
            "personal_info": {
                "name": "string",
                "email": "string",
                "phone": "string (optional)",
                "location": "string (optional)",
                "linkedin": "string (optional)",
                "github": "string (optional)"
            },
            "experience": [{
                "title": "string",
                "company": "string",
                "duration": "string (e.g., '2020-Present')",
                "location": "string (optional)",
                "description": "string",
                "achievements": ["string (quantified)"],
                "technologies": ["string"],
                "projects": [{
                    "title": "string",
                    "description": "string",
                    "achievements": ["string"],
                    "technologies": ["string"]
                }]
            }],
            "education": [{
                "degree": "string",
                "institution": "string",
                "year": "string",
                "location": "string (optional)"
            }],
            "skills": {
                "technical": ["string"],
                "soft": ["string (optional)"],
                "tools": ["string (optional)"],
                "frameworks": ["string (optional)"]
            }
        }
    
    def post(self, shared: dict, prep_res: dict, exec_res: List[dict]) -> str:
        """Store extracted experiences in shared store."""
        # Flatten all extracted experiences
        all_extracted = []
        successful_extractions = 0
        failed_extractions = 0
        
        for batch_result in exec_res:
            for extraction in batch_result:
                all_extracted.append(extraction)
                if extraction.get("extraction_confidence", 0) > 0.5:
                    successful_extractions += 1
                else:
                    failed_extractions += 1
        
        # Store in shared
        shared["extracted_experiences"] = all_extracted
        
        # Store summary statistics
        shared["extraction_summary"] = {
            "total_documents": len(all_extracted),
            "successful_extractions": successful_extractions,
            "failed_extractions": failed_extractions,
            "average_confidence": sum(e.get("extraction_confidence", 0) for e in all_extracted) / len(all_extracted) if all_extracted else 0
        }
        
        # Log summary
        logger.info(f"Experience extraction complete: {successful_extractions} successful, {failed_extractions} failed")
        if failed_extractions > 0:
            logger.warning(f"Failed to extract from {failed_extractions} documents")
        
        return "continue"


class BuildDatabaseNode(Node):
    """Builds structured career database from extracted experiences."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare extracted experiences for processing."""
        return {
            "extracted_experiences": shared.get("extracted_experiences", []),
            "existing_database": shared.get("existing_career_database"),
            "output_path": shared.get("database_output_path", "career_database.yaml"),
            "merge_strategy": shared.get("merge_strategy", "smart")  # smart, replace, append
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Build and deduplicate career database."""
        from utils.database_parser import validate_with_schema, save_career_database
        from datetime import datetime
        import re
        
        # 1. Aggregate all experiences from extracted documents
        all_data = self._aggregate_extractions(prep_res["extracted_experiences"])
        
        # 2. Deduplicate and merge experiences
        deduped_data = self._deduplicate_data(all_data)
        
        # 3. Structure into career database format
        career_db = self._build_database(deduped_data)
        
        # 4. Merge with existing database if provided
        if prep_res["existing_database"]:
            career_db = self._merge_with_existing(
                career_db, 
                prep_res["existing_database"], 
                prep_res["merge_strategy"]
            )
        
        # 5. Clean and standardize data
        career_db = self._clean_database(career_db)
        
        # 6. Validate against schema
        validation_errors = validate_with_schema(career_db)
        
        # 7. Generate summary report
        summary = self._generate_summary(
            career_db, 
            prep_res["extracted_experiences"],
            validation_errors
        )
        
        return {
            "career_database": career_db,
            "summary": summary,
            "validation_errors": validation_errors
        }
    
    def _aggregate_extractions(self, extracted_experiences):
        """Aggregate all extracted data from multiple documents."""
        aggregated = {
            "personal_info": {},
            "experiences": [],
            "education": [],
            "skills": {
                "technical": set(),
                "soft": set(),
                "languages": set(),
                "tools": set(),
                "frameworks": set(),
                "methodologies": set()
            },
            "projects": [],
            "certifications": [],
            "publications": [],
            "awards": []
        }
        
        for extraction in extracted_experiences:
            # Skip failed extractions
            if extraction.get("extraction_confidence", 0) < 0.3:
                continue
            
            # Aggregate personal info (prefer non-empty values)
            if extraction.get("personal_info"):
                for key, value in extraction["personal_info"].items():
                    if value and (not aggregated["personal_info"].get(key) or len(str(value)) > len(str(aggregated["personal_info"].get(key, "")))):
                        aggregated["personal_info"][key] = value
            
            # Collect experiences
            aggregated["experiences"].extend(extraction.get("experiences", []))
            
            # Collect education
            aggregated["education"].extend(extraction.get("education", []))
            
            # Aggregate skills (using sets to avoid duplicates)
            if extraction.get("skills"):
                for skill_type, skills in extraction["skills"].items():
                    if skill_type in aggregated["skills"] and isinstance(skills, list):
                        aggregated["skills"][skill_type].update(skills)
            
            # Collect other sections
            aggregated["projects"].extend(extraction.get("projects", []))
            aggregated["certifications"].extend(extraction.get("certifications", []))
            aggregated["publications"].extend(extraction.get("publications", []))
            aggregated["awards"].extend(extraction.get("awards", []))
        
        # Convert skill sets back to lists
        for skill_type in aggregated["skills"]:
            aggregated["skills"][skill_type] = sorted(list(aggregated["skills"][skill_type]))
        
        return aggregated
    
    def _deduplicate_data(self, aggregated_data):
        """Deduplicate experiences, projects, and other entries."""
        # Deduplicate experiences
        aggregated_data["experiences"] = self._deduplicate_experiences(
            aggregated_data["experiences"]
        )
        
        # Deduplicate education
        aggregated_data["education"] = self._deduplicate_education(
            aggregated_data["education"]
        )
        
        # Deduplicate standalone projects
        aggregated_data["projects"] = self._deduplicate_projects(
            aggregated_data["projects"]
        )
        
        # Deduplicate certifications
        aggregated_data["certifications"] = self._deduplicate_certifications(
            aggregated_data["certifications"]
        )
        
        return aggregated_data
    
    def _deduplicate_experiences(self, experiences):
        """Intelligently deduplicate work experiences."""
        from datetime import datetime
        
        if not experiences:
            return []
        
        # Group by company and approximate role
        grouped = {}
        for exp in experiences:
            # Create a key based on company and normalized title
            company_key = self._normalize_company_name(exp.get("company", ""))
            title_key = self._normalize_job_title(exp.get("title", ""))
            key = (company_key, title_key)
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(exp)
        
        # Merge each group
        deduped = []
        for key, group in grouped.items():
            if len(group) == 1:
                deduped.append(group[0])
            else:
                merged = self._merge_experience_group(group)
                deduped.append(merged)
        
        # Sort by start date (most recent first)
        deduped.sort(key=lambda x: self._parse_date_from_duration(x.get("duration", "")) or datetime(1900, 1, 1), reverse=True)
        
        return deduped
    
    def _merge_experience_group(self, experiences):
        """Merge multiple instances of the same experience."""
        # Use the most detailed one as base
        base = max(experiences, key=lambda x: (
            len(x.get("description", "")),
            len(x.get("achievements", [])),
            len(x.get("projects", []))
        ))
        
        # Create a copy to avoid modifying original
        merged = base.copy()
        
        # Merge achievements (unique)
        all_achievements = []
        for exp in experiences:
            all_achievements.extend(exp.get("achievements", []))
        merged["achievements"] = list(dict.fromkeys(all_achievements))  # Preserve order, remove duplicates
        
        # Merge technologies
        all_tech = []
        for exp in experiences:
            all_tech.extend(exp.get("technologies", []))
        merged["technologies"] = list(dict.fromkeys(all_tech))
        
        # Merge projects by title
        projects_by_title = {}
        for exp in experiences:
            for proj in exp.get("projects", []):
                title = proj.get("title", "")
                if title:
                    if title not in projects_by_title:
                        projects_by_title[title] = []
                    projects_by_title[title].append(proj)
        
        # Merge each project group
        merged_projects = []
        for title, proj_group in projects_by_title.items():
            if len(proj_group) == 1:
                merged_projects.append(proj_group[0])
            else:
                # Merge project details
                merged_proj = self._merge_project_group(proj_group)
                merged_projects.append(merged_proj)
        
        merged["projects"] = merged_projects
        
        # Use the most specific duration (prefer ones with month names)
        for exp in experiences:
            duration = exp.get("duration", "")
            if duration and (" - " in duration or any(month in duration.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])):
                merged["duration"] = duration
                break
        
        return merged
    
    def _merge_project_group(self, projects):
        """Merge multiple instances of the same project."""
        # Use most detailed as base
        base = max(projects, key=lambda x: len(x.get("description", "")))
        merged = base.copy()
        
        # Merge achievements
        all_achievements = []
        for proj in projects:
            all_achievements.extend(proj.get("achievements", []))
        merged["achievements"] = list(dict.fromkeys(all_achievements))
        
        # Merge technologies
        all_tech = []
        for proj in projects:
            all_tech.extend(proj.get("technologies", []))
        merged["technologies"] = list(dict.fromkeys(all_tech))
        
        return merged
    
    def _deduplicate_education(self, education_list):
        """Deduplicate education entries."""
        if not education_list:
            return []
        
        # Group by institution and degree
        seen = set()
        deduped = []
        
        for edu in education_list:
            key = (
                edu.get("institution", "").lower(),
                edu.get("degree", "").lower()
            )
            if key not in seen:
                seen.add(key)
                deduped.append(edu)
        
        return deduped
    
    def _deduplicate_projects(self, projects):
        """Deduplicate standalone projects."""
        if not projects:
            return []
        
        # Group by name
        seen = set()
        deduped = []
        
        for proj in projects:
            name = proj.get("name", "").lower()
            if name and name not in seen:
                seen.add(name)
                deduped.append(proj)
        
        return deduped
    
    def _deduplicate_certifications(self, certs):
        """Deduplicate certifications."""
        if not certs:
            return []
        
        # Group by name and issuer
        seen = set()
        deduped = []
        
        for cert in certs:
            key = (
                cert.get("name", "").lower(),
                cert.get("issuer", "").lower()
            )
            if key[0] and key not in seen:
                seen.add(key)
                deduped.append(cert)
        
        return deduped
    
    def _build_database(self, deduped_data):
        """Structure data into final career database format."""
        # Start with required sections
        career_db = {
            "personal_info": deduped_data["personal_info"] or {},
            "experience": deduped_data["experiences"],
            "education": deduped_data["education"],
            "skills": {}
        }
        
        # Add skills (filter out empty lists)
        for skill_type, skills in deduped_data["skills"].items():
            if skills:
                if skill_type == "technical" or skills:  # technical is required
                    career_db["skills"][skill_type] = skills
        
        # Add optional sections only if they have content
        if deduped_data["projects"]:
            career_db["projects"] = deduped_data["projects"]
        
        if deduped_data["certifications"]:
            career_db["certifications"] = deduped_data["certifications"]
        
        if deduped_data["publications"]:
            career_db["publications"] = deduped_data["publications"]
        
        if deduped_data["awards"]:
            career_db["awards"] = deduped_data["awards"]
        
        return career_db
    
    def _merge_with_existing(self, new_db, existing_db, strategy):
        """Merge new database with existing one based on strategy."""
        if strategy == "replace":
            return new_db
        elif strategy == "append":
            # Simple append - just concatenate lists
            from utils.database_parser import merge_career_databases
            return merge_career_databases(existing_db, new_db)
        else:  # smart merge
            # Use existing personal info if more complete
            if existing_db.get("personal_info"):
                for key, value in existing_db["personal_info"].items():
                    if value and not new_db.get("personal_info", {}).get(key):
                        if "personal_info" not in new_db:
                            new_db["personal_info"] = {}
                        new_db["personal_info"][key] = value
            
            # Merge experiences intelligently
            all_exp = existing_db.get("experience", []) + new_db.get("experience", [])
            new_db["experience"] = self._deduplicate_experiences(all_exp)
            
            # Merge education
            all_edu = existing_db.get("education", []) + new_db.get("education", [])
            new_db["education"] = self._deduplicate_education(all_edu)
            
            # Merge skills
            if "skills" in existing_db:
                for skill_type, skills in existing_db["skills"].items():
                    if skill_type in new_db.get("skills", {}):
                        combined = set(new_db["skills"][skill_type]) | set(skills)
                        new_db["skills"][skill_type] = sorted(list(combined))
                    else:
                        if "skills" not in new_db:
                            new_db["skills"] = {}
                        new_db["skills"][skill_type] = skills
            
            return new_db
    
    def _clean_database(self, career_db):
        """Clean and standardize the database."""
        import re
        
        # Clean personal info
        if "personal_info" in career_db:
            for key, value in career_db["personal_info"].items():
                if isinstance(value, str):
                    career_db["personal_info"][key] = value.strip()
        
        # Clean experiences
        for exp in career_db.get("experience", []):
            # Standardize dates
            if "duration" in exp:
                exp["duration"] = self._standardize_duration(exp["duration"])
            
            # Clean descriptions and achievements
            if "description" in exp:
                exp["description"] = exp["description"].strip()
            
            if "achievements" in exp:
                exp["achievements"] = [a.strip() for a in exp["achievements"] if a.strip()]
            
            # Clean technologies
            if "technologies" in exp:
                exp["technologies"] = self._standardize_technologies(exp["technologies"])
        
        # Standardize all technology lists
        if "skills" in career_db:
            for skill_type in ["technical", "tools", "frameworks"]:
                if skill_type in career_db["skills"]:
                    career_db["skills"][skill_type] = self._standardize_technologies(
                        career_db["skills"][skill_type]
                    )
        
        return career_db
    
    def _generate_summary(self, career_db, extracted_experiences, validation_errors):
        """Generate summary report of the build process."""
        summary = {
            "total_documents_processed": len(extracted_experiences),
            "successful_extractions": sum(
                1 for e in extracted_experiences 
                if e.get("extraction_confidence", 0) > 0.5
            ),
            "experiences_extracted": sum(
                len(e.get("experiences", [])) 
                for e in extracted_experiences
            ),
            "experiences_after_dedup": len(career_db.get("experience", [])),
            "companies": [],
            "technologies_found": [],
            "extraction_quality": {
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0
            },
            "validation_errors": validation_errors,
            "data_completeness": {}
        }
        
        # Count extraction quality
        for e in extracted_experiences:
            conf = e.get("extraction_confidence", 0)
            if conf >= 0.8:
                summary["extraction_quality"]["high_confidence"] += 1
            elif conf >= 0.5:
                summary["extraction_quality"]["medium_confidence"] += 1
            else:
                summary["extraction_quality"]["low_confidence"] += 1
        
        # Analyze companies and projects
        company_stats = {}
        for exp in career_db.get("experience", []):
            company = exp.get("company", "Unknown")
            if company not in company_stats:
                company_stats[company] = {"experiences": 0, "projects": 0}
            company_stats[company]["experiences"] += 1
            company_stats[company]["projects"] += len(exp.get("projects", []))
        
        summary["companies"] = [
            {"name": name, **stats} 
            for name, stats in company_stats.items()
        ]
        
        # Get all technologies
        from utils.database_parser import CareerDatabaseParser
        parser = CareerDatabaseParser()
        parser.data = career_db
        summary["technologies_found"] = parser.get_all_technologies()
        
        # Check data completeness
        summary["data_completeness"] = {
            "has_personal_info": bool(career_db.get("personal_info", {}).get("name")),
            "has_email": bool(career_db.get("personal_info", {}).get("email")),
            "has_experience": bool(career_db.get("experience")),
            "has_education": bool(career_db.get("education")),
            "has_skills": bool(career_db.get("skills", {}).get("technical")),
            "has_projects": bool(career_db.get("projects")) or any(
                exp.get("projects") for exp in career_db.get("experience", [])
            )
        }
        
        # Calculate date range
        dates = []
        for exp in career_db.get("experience", []):
            duration = exp.get("duration", "")
            if duration:
                start_date = self._parse_date_from_duration(duration)
                if start_date:
                    dates.append(start_date)
        
        if dates:
            summary["date_range"] = f"{min(dates).strftime('%Y-%m')} to present"
        
        return summary
    
    def _normalize_company_name(self, company):
        """Normalize company name for comparison."""
        # Remove common suffixes
        normalized = company.lower().strip()
        for suffix in [", inc.", ", inc", ", llc", ", ltd", ", corp", ", corporation"]:
            normalized = normalized.replace(suffix, "")
        return normalized
    
    def _normalize_job_title(self, title):
        """Normalize job title for comparison."""
        # Simplify common variations
        normalized = title.lower().strip()
        replacements = {
            "sr.": "senior",
            "sr ": "senior ",
            "jr.": "junior",
            "jr ": "junior ",
            "software engineer": "engineer",
            "software developer": "developer"
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        return normalized
    
    def _parse_date_from_duration(self, duration):
        """Parse start date from duration string."""
        from datetime import datetime
        import re
        
        # Match patterns like "2020-Present", "Jan 2020 - Dec 2023"
        patterns = [
            r'(\d{4})',  # Just year
            r'(\w{3})\s+(\d{4})',  # Mon YYYY
            r'(\d{1,2})/(\d{4})',  # MM/YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, duration)
            if match:
                try:
                    if len(match.groups()) == 1:
                        # Just year
                        return datetime(int(match.group(1)), 1, 1)
                    elif len(match.groups()) == 2:
                        # Month Year
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month = month_map.get(match.group(1).lower(), 1)
                        return datetime(int(match.group(2)), month, 1)
                except:
                    pass
        
        return None
    
    def _standardize_duration(self, duration):
        """Standardize duration format."""
        # Already in good format
        if " - " in duration or "-" in duration:
            return duration
        
        # Convert "Current" to "Present"
        duration = duration.replace("Current", "Present")
        duration = duration.replace("current", "Present")
        
        return duration
    
    def _standardize_technologies(self, tech_list):
        """Standardize technology names."""
        if not tech_list:
            return []
        
        # Common standardizations
        replacements = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "python": "Python",
            "react": "React",
            "react.js": "React",
            "reactjs": "React",
            "node.js": "Node.js",
            "nodejs": "Node.js",
            "mongodb": "MongoDB",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql": "MySQL",
            "aws": "AWS",
            "gcp": "Google Cloud Platform",
            "k8s": "Kubernetes"
        }
        
        standardized = []
        for tech in tech_list:
            tech_lower = tech.lower().strip()
            standardized.append(replacements.get(tech_lower, tech.strip()))
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(standardized))
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Save database and store in shared."""
        from utils.database_parser import save_career_database
        
        # Save to file
        save_career_database(exec_res["career_database"], prep_res["output_path"])
        
        # Store in shared
        shared["career_database"] = exec_res["career_database"]
        shared["build_summary"] = exec_res["summary"]
        
        if exec_res["validation_errors"]:
            shared["validation_errors"] = exec_res["validation_errors"]
            logger.warning(f"Validation errors: {exec_res['validation_errors']}")
        
        # Log summary
        logger.info(f"Career database built successfully:")
        logger.info(f"- Documents processed: {exec_res['summary']['total_documents_processed']}")
        logger.info(f"- Experiences: {exec_res['summary']['experiences_after_dedup']}")
        logger.info(f"- Companies: {len(exec_res['summary']['companies'])}")
        logger.info(f"- Technologies: {len(exec_res['summary']['technologies_found'])}")
        
        return "complete"