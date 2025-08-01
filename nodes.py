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