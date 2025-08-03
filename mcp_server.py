#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for Career Application Agent.

This server exposes the career agent's capabilities via MCP, allowing it to be used
as a sub-agent by Claude Desktop and other MCP-compatible clients.

The server supports two modes:
1. MCP Sampling Mode: Delegates LLM operations to the client via sampling requests
2. Standalone Mode: Uses API tokens for direct LLM access (when not running under MCP)
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastmcp import FastMCP, Context
    from fastmcp.resources import FileResource
    MCP_AVAILABLE = True
except ImportError:
    print("FastMCP not installed. Install with: pip install fastmcp")
    MCP_AVAILABLE = False
    FastMCP = None
    Context = None

from pocketflow import Flow
from nodes import (
    ScanDocumentsNode,
    ExtractExperienceNode,
    BuildDatabaseNode,
    ExtractRequirementsNode,
    AnalyzeFitNode,
    GenerateStrategyNode,
    GenerateCVNode,
    GenerateCoverLetterNode
)
from flow import ApplicationFlow, ExperienceDatabaseFlow
from utils.adaptive_llm_wrapper import AdaptiveLLMWrapper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
if MCP_AVAILABLE:
    mcp = FastMCP(
        "Career Application Agent",
        description="AI-powered career application assistant that helps with job applications"
    )
else:
    mcp = None


def get_data_dir() -> Path:
    """Get the data directory for storing agent outputs."""
    data_dir = Path.home() / ".career-agent"
    data_dir.mkdir(exist_ok=True)
    return data_dir


# Resource definitions - expose generated documents and databases
if mcp:
    @mcp.resource("career-database://current")
    async def get_career_database() -> str:
        """Get the current career database YAML."""
        db_path = get_data_dir() / "career_database.yaml"
        if db_path.exists():
            return db_path.read_text()
        return "No career database found. Build one first using the build_career_database tool."

    @mcp.resource("documents://cv/latest")
    async def get_latest_cv() -> str:
        """Get the most recently generated CV."""
        cv_dir = get_data_dir() / "generated_cvs"
        if cv_dir.exists():
            cv_files = sorted(cv_dir.glob("cv_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if cv_files:
                return cv_files[0].read_text()
        return "No CV found. Generate one first using the generate_cv tool."

    @mcp.resource("documents://cover-letter/latest")
    async def get_latest_cover_letter() -> str:
        """Get the most recently generated cover letter."""
        letter_dir = get_data_dir() / "generated_cover_letters"
        if letter_dir.exists():
            letter_files = sorted(
                letter_dir.glob("cover_letter_*.md"), 
                key=lambda p: p.stat().st_mtime, 
                reverse=True
            )
            if letter_files:
                return letter_files[0].read_text()
        return "No cover letter found. Generate one first using the generate_cover_letter tool."


# Tool definitions - expose agent capabilities
if mcp:
    @mcp.tool()
    async def build_career_database(
        documents_dir: str,
        ctx: Context
    ) -> Dict[str, Any]:
        """
        Build a career database from documents in the specified directory.
        
        This tool scans documents (PDFs, Word docs, text files) and extracts
        work experiences, skills, and achievements to build a comprehensive
        career database.
        
        Args:
            documents_dir: Path to directory containing career documents
            ctx: MCP context for sampling
            
        Returns:
            Summary of the built database
        """
        try:
            await ctx.info(f"Starting career database build from: {documents_dir}")
            
            # Create adaptive LLM wrapper that uses MCP sampling
            llm_wrapper = AdaptiveLLMWrapper(mcp_context=ctx)
            
            # Initialize flow with adaptive wrapper
            flow = ExperienceDatabaseFlow(llm_wrapper=llm_wrapper)
            
            # Prepare shared data
            shared_data = {
                "documents_directory": documents_dir,
                "output_directory": str(get_data_dir())
            }
            
            # Run the flow
            await ctx.info("Scanning documents...")
            result = flow.run(shared_data, max_iterations=50)
            
            if result.get("database_built"):
                summary = result.get("build_summary", {})
                await ctx.info(f"✅ Career database built successfully!")
                return {
                    "success": True,
                    "summary": summary,
                    "database_path": result.get("database_output_path"),
                    "message": f"Processed {summary.get('total_documents_processed', 0)} documents, "
                              f"extracted {summary.get('experiences_after_dedup', 0)} experiences"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to build career database",
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"Error building career database: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    async def analyze_job(
        job_url: str,
        job_description: str = None,
        ctx: Context
    ) -> Dict[str, Any]:
        """
        Analyze a job posting and assess fit based on career database.
        
        Args:
            job_url: URL of the job posting
            job_description: Optional job description text (if not provided, will attempt to fetch)
            ctx: MCP context for sampling
            
        Returns:
            Analysis results including fit score and recommendations
        """
        try:
            await ctx.info(f"Analyzing job posting: {job_url}")
            
            # Create adaptive LLM wrapper
            llm_wrapper = AdaptiveLLMWrapper(mcp_context=ctx)
            
            # Load career database
            db_path = get_data_dir() / "career_database.yaml"
            if not db_path.exists():
                return {
                    "success": False,
                    "error": "No career database found. Build one first using build_career_database."
                }
            
            # Create nodes with adaptive wrapper
            extract_node = ExtractRequirementsNode()
            extract_node.llm = llm_wrapper
            
            analyze_node = AnalyzeFitNode()
            analyze_node.llm = llm_wrapper
            
            # Prepare shared data
            import yaml
            career_db = yaml.safe_load(db_path.read_text())
            
            shared_data = {
                "job_url": job_url,
                "job_description": job_description or f"[Fetch from {job_url}]",
                "career_database": career_db
            }
            
            # Extract requirements
            await ctx.info("Extracting job requirements...")
            req_prep = extract_node.prep(shared_data)
            req_exec = extract_node.exec(req_prep)
            extract_node.post(shared_data, req_prep, req_exec)
            
            # Analyze fit
            await ctx.info("Analyzing candidate fit...")
            fit_prep = analyze_node.prep(shared_data)
            fit_exec = analyze_node.exec(fit_prep)
            analyze_node.post(shared_data, fit_prep, fit_exec)
            
            assessment = shared_data.get("fit_assessment", {})
            
            return {
                "success": True,
                "job_title": shared_data.get("job_requirements", {}).get("job_title"),
                "company": shared_data.get("company_name"),
                "technical_fit_score": assessment.get("technical_fit_score"),
                "cultural_fit_score": assessment.get("cultural_fit_score"),
                "overall_fit_score": assessment.get("overall_fit_score"),
                "key_strengths": assessment.get("key_strengths", []),
                "critical_gaps": assessment.get("critical_gaps", []),
                "recommendation": assessment.get("overall_recommendation")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing job: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    async def generate_cv(
        job_url: str,
        job_description: str = None,
        template: str = "default",
        ctx: Context
    ) -> Dict[str, Any]:
        """
        Generate a tailored CV for a specific job posting.
        
        Args:
            job_url: URL of the job posting
            job_description: Optional job description text
            template: CV template to use (default, technical, executive)
            ctx: MCP context for sampling
            
        Returns:
            Generated CV details and file path
        """
        try:
            await ctx.info(f"Generating tailored CV for: {job_url}")
            
            # Create adaptive LLM wrapper
            llm_wrapper = AdaptiveLLMWrapper(mcp_context=ctx)
            
            # First analyze the job if not already done
            job_analysis = await analyze_job(job_url, job_description, ctx)
            if not job_analysis["success"]:
                return job_analysis
            
            # Create CV generation node
            cv_node = GenerateCVNode()
            cv_node.llm = llm_wrapper
            
            # Prepare shared data
            db_path = get_data_dir() / "career_database.yaml"
            import yaml
            career_db = yaml.safe_load(db_path.read_text())
            
            shared_data = {
                "job_url": job_url,
                "job_title": job_analysis["job_title"],
                "company_name": job_analysis["company"],
                "career_database": career_db,
                "cv_template": template,
                "fit_assessment": {
                    "key_strengths": job_analysis["key_strengths"],
                    "critical_gaps": job_analysis["critical_gaps"]
                }
            }
            
            # Generate CV
            await ctx.info("Generating personalized CV...")
            cv_prep = cv_node.prep(shared_data)
            cv_exec = cv_node.exec(cv_prep)
            cv_node.post(shared_data, cv_prep, cv_exec)
            
            # Save CV
            cv_dir = get_data_dir() / "generated_cvs"
            cv_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv_path = cv_dir / f"cv_{job_analysis['company']}_{timestamp}.md"
            cv_path.write_text(shared_data["generated_cv"])
            
            await ctx.info(f"✅ CV generated successfully: {cv_path}")
            
            return {
                "success": True,
                "cv_path": str(cv_path),
                "job_title": job_analysis["job_title"],
                "company": job_analysis["company"],
                "preview": shared_data["generated_cv"][:500] + "..."
            }
            
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    async def generate_cover_letter(
        job_url: str,
        job_description: str = None,
        tone: str = "professional",
        ctx: Context
    ) -> Dict[str, Any]:
        """
        Generate a tailored cover letter for a specific job posting.
        
        Args:
            job_url: URL of the job posting
            job_description: Optional job description text
            tone: Writing tone (professional, enthusiastic, conversational)
            ctx: MCP context for sampling
            
        Returns:
            Generated cover letter details and file path
        """
        try:
            await ctx.info(f"Generating tailored cover letter for: {job_url}")
            
            # Create adaptive LLM wrapper
            llm_wrapper = AdaptiveLLMWrapper(mcp_context=ctx)
            
            # First analyze the job if not already done
            job_analysis = await analyze_job(job_url, job_description, ctx)
            if not job_analysis["success"]:
                return job_analysis
            
            # Create cover letter generation node
            letter_node = GenerateCoverLetterNode()
            letter_node.llm = llm_wrapper
            
            # Prepare shared data
            db_path = get_data_dir() / "career_database.yaml"
            import yaml
            career_db = yaml.safe_load(db_path.read_text())
            
            shared_data = {
                "job_url": job_url,
                "job_title": job_analysis["job_title"],
                "company_name": job_analysis["company"],
                "career_database": career_db,
                "cover_letter_tone": tone,
                "fit_assessment": {
                    "key_strengths": job_analysis["key_strengths"],
                    "unique_value_proposition": job_analysis.get("recommendation", "")
                },
                "application_strategy": {
                    "key_themes": ["technical excellence", "leadership", "innovation"]
                }
            }
            
            # Generate cover letter
            await ctx.info("Generating personalized cover letter...")
            letter_prep = letter_node.prep(shared_data)
            letter_exec = letter_node.exec(letter_prep)
            letter_node.post(shared_data, letter_prep, letter_exec)
            
            # Save cover letter
            letter_dir = get_data_dir() / "generated_cover_letters"
            letter_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            letter_path = letter_dir / f"cover_letter_{job_analysis['company']}_{timestamp}.md"
            letter_path.write_text(shared_data["generated_cover_letter"])
            
            await ctx.info(f"✅ Cover letter generated successfully: {letter_path}")
            
            return {
                "success": True,
                "cover_letter_path": str(letter_path),
                "job_title": job_analysis["job_title"],
                "company": job_analysis["company"],
                "preview": shared_data["generated_cover_letter"][:500] + "..."
            }
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    async def full_application_workflow(
        job_url: str,
        documents_dir: str = None,
        ctx: Context
    ) -> Dict[str, Any]:
        """
        Run the complete application workflow: build database, analyze job, generate documents.
        
        Args:
            job_url: URL of the job posting
            documents_dir: Optional directory for career documents (uses existing DB if not provided)
            ctx: MCP context for sampling
            
        Returns:
            Complete workflow results
        """
        try:
            results = {}
            
            # Step 1: Build or verify career database
            if documents_dir:
                await ctx.info("Step 1: Building career database...")
                db_result = await build_career_database(documents_dir, ctx)
                results["database"] = db_result
                if not db_result["success"]:
                    return results
            else:
                db_path = get_data_dir() / "career_database.yaml"
                if not db_path.exists():
                    return {
                        "success": False,
                        "error": "No career database found. Provide documents_dir to build one."
                    }
                await ctx.info("Using existing career database")
            
            # Step 2: Analyze job
            await ctx.info("Step 2: Analyzing job posting...")
            analysis_result = await analyze_job(job_url, None, ctx)
            results["analysis"] = analysis_result
            if not analysis_result["success"]:
                return results
            
            # Step 3: Generate CV
            await ctx.info("Step 3: Generating tailored CV...")
            cv_result = await generate_cv(job_url, None, "default", ctx)
            results["cv"] = cv_result
            
            # Step 4: Generate cover letter
            await ctx.info("Step 4: Generating cover letter...")
            letter_result = await generate_cover_letter(job_url, None, "professional", ctx)
            results["cover_letter"] = letter_result
            
            # Summary
            await ctx.info("✅ Application workflow completed!")
            results["success"] = True
            results["summary"] = {
                "job_title": analysis_result["job_title"],
                "company": analysis_result["company"],
                "fit_score": analysis_result["overall_fit_score"],
                "documents_generated": [
                    cv_result.get("cv_path"),
                    letter_result.get("cover_letter_path")
                ]
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in application workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "partial_results": results
            }


# Prompts - pre-defined templates for common workflows
if mcp:
    @mcp.prompt()
    async def help_me_apply() -> str:
        """Get started with a job application."""
        return """I'll help you apply for a job! Here's what I can do:

1. **Build your career database** from your existing documents (resume, CV, etc.)
2. **Analyze the job posting** to understand requirements and assess fit
3. **Generate a tailored CV** optimized for the specific role
4. **Create a compelling cover letter** that highlights your strengths

To get started, I'll need:
- The job posting URL
- The location of your career documents (if we haven't built your database yet)

Would you like me to:
- Run the complete workflow for a specific job?
- Start by building your career database?
- Analyze a specific job posting?

Just let me know the job URL and I'll help you create a winning application!"""

    @mcp.prompt()
    async def update_my_database() -> str:
        """Update career database with new experiences."""
        return """I can help you update your career database with new experiences!

Please provide:
1. The directory containing your updated career documents
2. Any specific new experiences or achievements you'd like to highlight

I'll scan your documents and update the database with:
- New work experiences
- Additional skills and technologies
- Recent achievements and projects
- Updated education or certifications

Just tell me where your documents are located and I'll rebuild your career database."""


# Main entry point
if __name__ == "__main__":
    if not MCP_AVAILABLE:
        print("FastMCP is required to run the MCP server")
        print("Install with: pip install fastmcp")
        sys.exit(1)
    
    # Run the MCP server
    mcp.run()