"""
Async versions of nodes for parallel LLM processing.

This module provides async implementations of nodes that benefit from
parallel LLM calls, significantly improving performance.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pocketflow import AsyncParallelBatchNode

logger = logging.getLogger(__name__)


class AsyncExtractExperienceNode(AsyncParallelBatchNode):
    """
    Async version of ExtractExperienceNode for parallel document processing.
    
    Processes multiple documents in parallel using async LLM calls,
    significantly reducing total processing time.
    """
    
    def __init__(self, async_llm_wrapper=None, max_concurrent: int = 5):
        """
        Initialize async extract experience node.
        
        Args:
            async_llm_wrapper: Async LLM wrapper instance
            max_concurrent: Maximum concurrent LLM calls
        """
        super().__init__(max_retries=3, wait=2)
        
        if async_llm_wrapper is None:
            from utils.async_llm_wrapper import get_async_llm_wrapper
            self.llm = asyncio.run(get_async_llm_wrapper())
        else:
            self.llm = async_llm_wrapper
        
        self.max_concurrent = max_concurrent
    
    async def prep_async(self, shared: dict) -> List[dict]:
        """Prepare documents for async processing."""
        documents = shared.get("document_sources", [])
        
        # Load career schema if available
        career_schema = shared.get("career_database_schema")
        if not career_schema:
            career_schema = self._get_default_career_schema()
        
        # Return list of items to process in parallel
        return [
            {
                "document": doc,
                "career_schema": career_schema,
                "extraction_mode": shared.get("extraction_mode", "comprehensive")
            }
            for doc in documents
        ]
    
    async def exec_async(self, item: dict) -> dict:
        """Process single document asynchronously."""
        from utils.document_parser import parse_document
        import json
        
        doc = item["document"]
        career_schema = item["career_schema"]
        extraction_mode = item["extraction_mode"]
        
        try:
            # Parse document (this is still sync for now)
            logger.info(f"Parsing document: {doc['name']}")
            parsed = await asyncio.get_event_loop().run_in_executor(
                None,
                parse_document,
                doc['path'],
                'auto'
            )
            
            if parsed.error:
                logger.error(f"Failed to parse {doc['name']}: {parsed.error}")
                return {
                    "document_source": doc['path'],
                    "document_name": doc['name'],
                    "extraction_confidence": 0.0,
                    "error": parsed.error,
                    "experiences": []
                }
            
            # Classify document type
            doc_type = await self._classify_document_async(
                parsed.text[:3000], doc['name']
            )
            
            # Create extraction prompt
            system_prompt = self._create_system_prompt(career_schema, doc_type)
            user_prompt = self._create_user_prompt(
                parsed.text, doc_type, extraction_mode
            )
            
            # Extract experiences using async LLM
            logger.info(f"Extracting experiences from {doc['name']} using async LLM")
            
            extracted_data = await self.llm.call_llm_structured(
                prompt=user_prompt,
                system_prompt=system_prompt,
                output_format="yaml",
                temperature=0.3,
                max_tokens=4000
            )
            
            # Calculate confidence
            confidence = self._calculate_extraction_confidence(
                extracted_data, doc_type
            )
            
            # Structure the result
            result = {
                "document_source": doc['path'],
                "document_name": doc['name'],
                "document_type": doc_type,
                "extraction_confidence": confidence,
                "parsed_text_length": len(parsed.text),
                "experiences": self._structure_extraction(extracted_data, doc_type)
            }
            
            logger.info(
                f"Successfully extracted {len(result['experiences'])} "
                f"experiences from {doc['name']} (confidence: {confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting from {doc['name']}: {e}")
            return {
                "document_source": doc['path'],
                "document_name": doc['name'],
                "extraction_confidence": 0.0,
                "error": str(e),
                "experiences": []
            }
    
    async def post_async(
        self,
        shared: dict,
        prep_res: List[dict],
        exec_res: List[dict]
    ) -> Optional[str]:
        """Store extracted experiences in shared store."""
        # Filter out failed extractions
        successful = [r for r in exec_res if r and not r.get("error")]
        failed = [r for r in exec_res if r and r.get("error")]
        
        logger.info(
            f"Extraction complete: {len(successful)} successful, "
            f"{len(failed)} failed out of {len(exec_res)} documents"
        )
        
        # Store results
        shared["extracted_experiences"] = exec_res
        shared["extraction_summary"] = {
            "total_documents": len(exec_res),
            "successful_extractions": len(successful),
            "failed_extractions": len(failed),
            "total_experiences": sum(
                len(r.get("experiences", [])) for r in successful
            )
        }
        
        return "default"
    
    async def _classify_document_async(
        self,
        text_sample: str,
        filename: str
    ) -> str:
        """Classify document type using async LLM."""
        prompt = f"""Classify this document based on its content and filename.

Filename: {filename}

Text sample:
{text_sample}

Classify as one of:
- resume: A resume or CV
- portfolio: Project portfolio or case studies
- job_description: A job posting
- cover_letter: A cover letter
- reference: Reference letter or recommendation
- other: Other document type

Respond with just the classification."""

        response = await self.llm.call_llm(
            prompt=prompt,
            temperature=0.1,
            max_tokens=50
        )
        
        doc_type = response.strip().lower()
        if doc_type not in [
            "resume", "portfolio", "job_description",
            "cover_letter", "reference", "other"
        ]:
            doc_type = "other"
        
        return doc_type
    
    def _get_default_career_schema(self) -> dict:
        """Get default career database schema."""
        return {
            "work_experience": {
                "company": "string",
                "title": "string",
                "start_date": "YYYY-MM",
                "end_date": "YYYY-MM or null",
                "location": "string (optional)",
                "employment_type": "string (optional)",
                "description": "string (optional)",
                "responsibilities": ["string"],
                "achievements": [
                    {
                        "description": "string",
                        "metrics": ["string"]
                    }
                ],
                "technologies": ["string"],
                "projects": [
                    {
                        "name": "string",
                        "role": "string",
                        "description": "string",
                        "technologies": ["string"],
                        "outcomes": ["string"]
                    }
                ]
            }
        }
    
    def _create_system_prompt(self, career_schema: dict, doc_type: str) -> str:
        """Create system prompt for extraction."""
        return f"""You are an expert at extracting structured work experience information from {doc_type} documents.

Extract work experiences following this schema:
{career_schema}

Guidelines:
- Extract ALL work experiences found in the document
- Preserve specific metrics and quantifiable achievements
- Maintain chronological order (most recent first)
- Include all mentioned technologies and tools
- Extract project details when available
- Use null for missing end dates (current positions)
- Format dates as YYYY-MM when possible"""
    
    def _create_user_prompt(
        self,
        text: str,
        doc_type: str,
        extraction_mode: str
    ) -> str:
        """Create user prompt for extraction."""
        # Truncate very long documents
        max_length = 15000 if extraction_mode == "comprehensive" else 8000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Document truncated for processing]"
        
        return f"""Extract all work experiences from this {doc_type}:

{text}

Return the extracted information as a YAML list of work experiences.
Each experience should include all available information from the schema.
Be thorough and extract all details, especially quantifiable achievements and project outcomes."""
    
    def _calculate_extraction_confidence(
        self,
        extracted_data: Any,
        doc_type: str
    ) -> float:
        """Calculate confidence score for extraction."""
        if not extracted_data or not isinstance(extracted_data, list):
            return 0.0
        
        # Base confidence by document type
        base_confidence = {
            "resume": 0.9,
            "portfolio": 0.85,
            "job_description": 0.0,  # Shouldn't extract from job descriptions
            "cover_letter": 0.7,
            "reference": 0.6,
            "other": 0.5
        }.get(doc_type, 0.5)
        
        # Adjust based on extraction quality
        if len(extracted_data) == 0:
            return 0.0
        
        # Check completeness of first experience
        if len(extracted_data) > 0:
            first_exp = extracted_data[0]
            required_fields = ["company", "title", "start_date"]
            present_fields = sum(1 for f in required_fields if f in first_exp)
            completeness = present_fields / len(required_fields)
            
            return base_confidence * completeness
        
        return base_confidence
    
    def _structure_extraction(
        self,
        extracted_data: Any,
        doc_type: str
    ) -> List[dict]:
        """Structure extracted data into consistent format."""
        if not isinstance(extracted_data, list):
            return []
        
        experiences = []
        for exp in extracted_data:
            if isinstance(exp, dict) and "company" in exp:
                # Ensure all fields have proper types
                structured_exp = {
                    "company": str(exp.get("company", "")),
                    "title": str(exp.get("title", "")),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date"),
                    "location": exp.get("location"),
                    "employment_type": exp.get("employment_type"),
                    "description": exp.get("description"),
                    "responsibilities": exp.get("responsibilities", []),
                    "achievements": exp.get("achievements", []),
                    "technologies": exp.get("technologies", []),
                    "projects": exp.get("projects", [])
                }
                experiences.append(structured_exp)
        
        return experiences


class AsyncGenerationFlow(AsyncParallelBatchNode):
    """
    Async version of document generation for parallel CV and cover letter creation.
    """
    
    def __init__(self, async_llm_wrapper=None):
        """Initialize async generation flow."""
        super().__init__()
        
        if async_llm_wrapper is None:
            from utils.async_llm_wrapper import get_async_llm_wrapper
            self.llm = asyncio.run(get_async_llm_wrapper())
        else:
            self.llm = async_llm_wrapper
    
    async def prep_async(self, shared: dict) -> List[dict]:
        """Prepare generation tasks."""
        # Return list of generation tasks
        tasks = []
        
        if shared.get("generate_cv", True):
            tasks.append({
                "type": "cv",
                "template": shared.get("cv_template", "default"),
                "data": shared.get("cv_data", {})
            })
        
        if shared.get("generate_cover_letter", True):
            tasks.append({
                "type": "cover_letter",
                "template": shared.get("cover_letter_template", "default"),
                "data": shared.get("cover_letter_data", {})
            })
        
        return tasks
    
    async def exec_async(self, task: dict) -> dict:
        """Generate document asynchronously."""
        doc_type = task["type"]
        template = task["template"]
        data = task["data"]
        
        try:
            if doc_type == "cv":
                content = await self._generate_cv_async(data, template)
            elif doc_type == "cover_letter":
                content = await self._generate_cover_letter_async(data, template)
            else:
                raise ValueError(f"Unknown document type: {doc_type}")
            
            return {
                "type": doc_type,
                "content": content,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating {doc_type}: {e}")
            return {
                "type": doc_type,
                "error": str(e),
                "success": False
            }
    
    async def _generate_cv_async(self, data: dict, template: str) -> str:
        """Generate CV using async LLM."""
        # Implementation would go here
        # This is a placeholder
        prompt = f"Generate a CV using template '{template}' with data: {data}"
        return await self.llm.call_llm(prompt)
    
    async def _generate_cover_letter_async(self, data: dict, template: str) -> str:
        """Generate cover letter using async LLM."""
        # Implementation would go here
        # This is a placeholder
        prompt = f"Generate a cover letter using template '{template}' with data: {data}"
        return await self.llm.call_llm(prompt)
    
    async def post_async(
        self,
        shared: dict,
        prep_res: List[dict],
        exec_res: List[dict]
    ) -> Optional[str]:
        """Store generated documents."""
        for result in exec_res:
            if result["success"]:
                if result["type"] == "cv":
                    shared["generated_cv"] = result["content"]
                elif result["type"] == "cover_letter":
                    shared["generated_cover_letter"] = result["content"]
        
        return "default"