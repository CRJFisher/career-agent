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


# Document Processing Nodes

class ScanDocumentsNode(Node):
    """
    Scans Google Drive and local directories for career-related documents.
    
    Discovers all relevant documents that contain work experience information
    for building the career database.
    """
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Get scan configuration from shared store."""
        config = shared.get("scan_config", {})
        if not config:
            # Default configuration
            config = {
                "local_paths": ["~/Documents/Resume", "~/Documents/Work"],
                "google_drive_folders": [],
                "file_types": [".pdf", ".md", ".docx", ".txt"]
            }
        return config
    
    def exec(self, config: Dict[str, Any]) -> list:
        """Scan for documents based on configuration."""
        # TODO: Implement actual scanning
        # Would use document_scanner utility
        return [
            {
                "path": "example.pdf",
                "type": "pdf",
                "source": "local",
                "modified": "2024-01-01"
            }
        ]
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: list) -> Optional[str]:
        """Store document list in shared store."""
        shared["document_sources"] = exec_res
        logger.info(f"Found {len(exec_res)} documents to process")
        return "default"


class ExtractExperienceNode(BatchNode):
    """
    Extracts work experience from discovered documents.
    
    Uses document parsers and LLM to extract structured work experience
    matching the enhanced career database schema.
    """
    
    def __init__(self):
        super().__init__(max_retries=3, wait=2)
        self.llm = get_default_llm_wrapper()
    
    def prep(self, shared: Dict[str, Any]) -> list:
        """Get list of documents to process."""
        return shared.get("document_sources", [])
    
    def exec(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract experience from a single document."""
        # TODO: Implement actual extraction
        # Would use document parser and LLM
        return {
            "source": document["path"],
            "experiences": []
        }
    
    def post(self, shared: Dict[str, Any], prep_res: list, exec_res_list: list) -> Optional[str]:
        """Store all extracted experiences."""
        shared["extracted_experiences"] = exec_res_list
        return "default"


# Workflow Management Nodes

class SaveCheckpointNode(Node):
    """
    Saves workflow state to checkpoint files for user review.
    
    Exports specific data to user-editable YAML files and pauses
    the workflow for manual review and editing.
    """
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what to save based on flow context."""
        # Get flow name from params or shared
        flow_name = self.params.get("flow_name", "workflow")
        
        # Determine which data to export based on flow
        export_config = {
            "flow_name": flow_name,
            "timestamp": None,  # Will be set in exec
            "export_fields": []
        }
        
        if flow_name == "analysis":
            export_config["export_fields"] = [
                "requirement_mapping",
                "strengths", 
                "gaps"
            ]
        elif flow_name == "narrative":
            export_config["export_fields"] = [
                "experience_priorities",
                "narrative_strategy",
                "themes"
            ]
            
        return export_config
    
    def exec(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save checkpoint and user-editable files."""
        import time
        import yaml
        from pathlib import Path
        
        timestamp = int(time.time())
        config["timestamp"] = timestamp
        
        # Create directories
        Path("checkpoints").mkdir(exist_ok=True)
        Path("outputs").mkdir(exist_ok=True)
        
        # Save checkpoint
        checkpoint_file = f"checkpoints/{config['flow_name']}_{timestamp}.yaml"
        output_file = f"outputs/{config['flow_name']}_output.yaml"
        
        return {
            "checkpoint_file": checkpoint_file,
            "output_file": output_file,
            "config": config
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> Optional[str]:
        """Save files and pause workflow."""
        import yaml
        
        # Save full checkpoint
        with open(exec_res["checkpoint_file"], 'w') as f:
            yaml.dump(shared, f)
        
        # Save user-editable output
        output_data = {
            "# Instructions": "Edit this file and save. The workflow will resume with your changes.",
            "# Flow": exec_res["config"]["flow_name"],
            "# Timestamp": exec_res["config"]["timestamp"]
        }
        
        for field in exec_res["config"]["export_fields"]:
            if field in shared:
                output_data[field] = shared[field]
        
        with open(exec_res["output_file"], 'w') as f:
            yaml.dump(output_data, f, sort_keys=False)
        
        logger.info(f"Checkpoint saved. Please review and edit: {exec_res['output_file']}")
        return "pause"  # Special action to indicate workflow should pause


class LoadCheckpointNode(Node):
    """
    Loads checkpoint and merges user edits to resume workflow.
    
    Reads the checkpoint file and user-edited output file,
    merging changes back into the shared store.
    """
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which checkpoint to load."""
        # Could get from params or auto-detect latest
        flow_name = self.params.get("flow_name", "workflow")
        return {"flow_name": flow_name}
    
    def exec(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load checkpoint and user edits."""
        import yaml
        from pathlib import Path
        
        # Find latest checkpoint for this flow
        checkpoint_dir = Path("checkpoints")
        checkpoints = list(checkpoint_dir.glob(f"{config['flow_name']}_*.yaml"))
        
        if not checkpoints:
            raise FileNotFoundError(f"No checkpoints found for {config['flow_name']}")
        
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        
        # Load checkpoint
        with open(latest, 'r') as f:
            checkpoint_data = yaml.safe_load(f)
        
        # Load user edits
        output_file = f"outputs/{config['flow_name']}_output.yaml"
        if Path(output_file).exists():
            with open(output_file, 'r') as f:
                user_data = yaml.safe_load(f)
        else:
            user_data = {}
        
        return {
            "checkpoint": checkpoint_data,
            "user_edits": user_data,
            "checkpoint_file": str(latest)
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> Optional[str]:
        """Merge checkpoint and user edits into shared store."""
        # Start with checkpoint data
        shared.update(exec_res["checkpoint"])
        
        # Apply user edits (they take precedence)
        for key, value in exec_res["user_edits"].items():
            if not key.startswith("#"):  # Skip comment fields
                shared[key] = value
                logger.info(f"Applied user edit to field: {key}")
        
        return "default"


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