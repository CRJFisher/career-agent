"""
FastAPI backend for Career Application Agent.

This module provides a web API interface for the career agent functionality,
including real-time updates via WebSockets.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
from utils.llm_wrapper import get_default_llm_wrapper

# Global storage for active workflows and connections
active_workflows: Dict[str, Dict[str, Any]] = {}
active_connections: Dict[str, List[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("Starting Career Agent API...")
    yield
    # Shutdown
    print("Shutting down Career Agent API...")
    # Clean up any resources


# Create FastAPI app
app = FastAPI(
    title="Career Application Agent API",
    description="AI-powered career application assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class BuildDatabaseRequest(BaseModel):
    """Request model for building career database."""
    documents_directory: str = Field(..., description="Path to documents directory")


class BuildDatabaseResponse(BaseModel):
    """Response model for database build."""
    success: bool
    workflow_id: str
    message: str
    summary: Optional[Dict[str, Any]] = None


class AnalyzeJobRequest(BaseModel):
    """Request model for job analysis."""
    job_url: str = Field(..., description="URL of job posting")
    job_description: Optional[str] = Field(None, description="Job description text")


class JobAnalysisResponse(BaseModel):
    """Response model for job analysis."""
    success: bool
    workflow_id: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    technical_fit_score: Optional[int] = None
    cultural_fit_score: Optional[int] = None
    overall_fit_score: Optional[int] = None


class GenerateDocumentRequest(BaseModel):
    """Request model for document generation."""
    job_url: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    document_type: str = Field(..., pattern="^(cv|cover_letter)$")
    template: Optional[str] = "default"
    tone: Optional[str] = "professional"


class WorkflowStatus(BaseModel):
    """Workflow status model."""
    workflow_id: str
    status: str
    progress: int
    current_step: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]


# Utility functions
def get_data_dir() -> Path:
    """Get the data directory for storing agent outputs."""
    data_dir = Path.home() / ".career-agent"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_upload_dir() -> Path:
    """Get the upload directory for temporary files."""
    upload_dir = get_data_dir() / "uploads"
    upload_dir.mkdir(exist_ok=True)
    return upload_dir


async def notify_workflow_update(workflow_id: str, message: Dict[str, Any]):
    """Send update to all connected clients for a workflow."""
    if workflow_id in active_connections:
        for websocket in active_connections[workflow_id]:
            try:
                await websocket.send_json(message)
            except:
                # Remove dead connections
                active_connections[workflow_id].remove(websocket)


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Career Application Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Career Database endpoints
@app.get("/api/database")
async def get_career_database():
    """Get the current career database."""
    db_path = get_data_dir() / "career_database.yaml"
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="No career database found")
    
    import yaml
    with open(db_path) as f:
        database = yaml.safe_load(f)
    
    return {
        "success": True,
        "database": database,
        "last_modified": datetime.fromtimestamp(db_path.stat().st_mtime)
    }


@app.post("/api/database/build", response_model=BuildDatabaseResponse)
async def build_career_database(
    request: BuildDatabaseRequest,
    background_tasks: BackgroundTasks
):
    """Build career database from documents."""
    workflow_id = str(uuid.uuid4())
    
    # Validate directory
    docs_dir = Path(request.documents_directory)
    if not docs_dir.exists():
        raise HTTPException(status_code=400, detail="Documents directory not found")
    
    # Start workflow in background
    background_tasks.add_task(
        run_database_build_workflow,
        workflow_id,
        str(docs_dir)
    )
    
    # Store workflow info
    active_workflows[workflow_id] = {
        "type": "database_build",
        "status": "started",
        "progress": 0,
        "started_at": datetime.utcnow()
    }
    
    return BuildDatabaseResponse(
        success=True,
        workflow_id=workflow_id,
        message="Database build started"
    )


async def run_database_build_workflow(workflow_id: str, documents_dir: str):
    """Run the database build workflow."""
    try:
        # Update status
        active_workflows[workflow_id]["status"] = "running"
        await notify_workflow_update(workflow_id, {
            "type": "status",
            "data": {"status": "running", "progress": 10}
        })
        
        # Create flow
        llm = get_default_llm_wrapper()
        flow = ExperienceDatabaseFlow(llm_wrapper=llm)
        
        # Prepare shared data
        shared_data = {
            "documents_directory": documents_dir,
            "output_directory": str(get_data_dir())
        }
        
        # Run flow with progress updates
        result = flow.run(shared_data, max_iterations=50)
        
        # Update final status
        if result.get("database_built"):
            active_workflows[workflow_id]["status"] = "completed"
            active_workflows[workflow_id]["result"] = result.get("build_summary")
            active_workflows[workflow_id]["progress"] = 100
            
            await notify_workflow_update(workflow_id, {
                "type": "completed",
                "data": {
                    "status": "completed",
                    "progress": 100,
                    "result": result.get("build_summary")
                }
            })
        else:
            raise Exception("Failed to build database")
            
    except Exception as e:
        active_workflows[workflow_id]["status"] = "failed"
        active_workflows[workflow_id]["error"] = str(e)
        
        await notify_workflow_update(workflow_id, {
            "type": "error",
            "data": {"status": "failed", "error": str(e)}
        })


# Job Analysis endpoints
@app.post("/api/jobs/analyze", response_model=JobAnalysisResponse)
async def analyze_job(
    request: AnalyzeJobRequest,
    background_tasks: BackgroundTasks
):
    """Analyze a job posting."""
    workflow_id = str(uuid.uuid4())
    
    # Check if database exists
    db_path = get_data_dir() / "career_database.yaml"
    if not db_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Career database not found. Build database first."
        )
    
    # Start workflow in background
    background_tasks.add_task(
        run_job_analysis_workflow,
        workflow_id,
        request.job_url,
        request.job_description
    )
    
    # Store workflow info
    active_workflows[workflow_id] = {
        "type": "job_analysis",
        "status": "started",
        "progress": 0,
        "job_url": request.job_url,
        "started_at": datetime.utcnow()
    }
    
    return JobAnalysisResponse(
        success=True,
        workflow_id=workflow_id
    )


async def run_job_analysis_workflow(
    workflow_id: str,
    job_url: str,
    job_description: Optional[str]
):
    """Run job analysis workflow."""
    try:
        # Update status
        active_workflows[workflow_id]["status"] = "running"
        await notify_workflow_update(workflow_id, {
            "type": "status",
            "data": {"status": "extracting_requirements", "progress": 20}
        })
        
        # Load career database
        import yaml
        db_path = get_data_dir() / "career_database.yaml"
        with open(db_path) as f:
            career_db = yaml.safe_load(f)
        
        # Create nodes
        llm = get_default_llm_wrapper()
        extract_node = ExtractRequirementsNode()
        analyze_node = AnalyzeFitNode()
        
        # Prepare shared data
        shared_data = {
            "job_url": job_url,
            "job_description": job_description or f"[Fetch from {job_url}]",
            "career_database": career_db
        }
        
        # Extract requirements
        await notify_workflow_update(workflow_id, {
            "type": "progress",
            "data": {"step": "Extracting job requirements", "progress": 30}
        })
        
        req_prep = extract_node.prep(shared_data)
        req_exec = extract_node.exec(req_prep)
        extract_node.post(shared_data, req_prep, req_exec)
        
        # Analyze fit
        await notify_workflow_update(workflow_id, {
            "type": "progress",
            "data": {"step": "Analyzing candidate fit", "progress": 60}
        })
        
        fit_prep = analyze_node.prep(shared_data)
        fit_exec = analyze_node.exec(fit_prep)
        analyze_node.post(shared_data, fit_prep, fit_exec)
        
        # Store results
        assessment = shared_data.get("fit_assessment", {})
        result = {
            "job_title": shared_data.get("job_requirements", {}).get("job_title"),
            "company": shared_data.get("company_name"),
            "technical_fit_score": assessment.get("technical_fit_score"),
            "cultural_fit_score": assessment.get("cultural_fit_score"),
            "overall_fit_score": assessment.get("overall_fit_score"),
            "key_strengths": assessment.get("key_strengths", []),
            "critical_gaps": assessment.get("critical_gaps", []),
            "recommendation": assessment.get("overall_recommendation")
        }
        
        active_workflows[workflow_id]["status"] = "completed"
        active_workflows[workflow_id]["result"] = result
        active_workflows[workflow_id]["progress"] = 100
        
        await notify_workflow_update(workflow_id, {
            "type": "completed",
            "data": {
                "status": "completed",
                "progress": 100,
                "result": result
            }
        })
        
    except Exception as e:
        active_workflows[workflow_id]["status"] = "failed"
        active_workflows[workflow_id]["error"] = str(e)
        
        await notify_workflow_update(workflow_id, {
            "type": "error",
            "data": {"status": "failed", "error": str(e)}
        })


# Document Generation endpoints
@app.post("/api/documents/generate")
async def generate_document(
    request: GenerateDocumentRequest,
    background_tasks: BackgroundTasks
):
    """Generate CV or cover letter."""
    workflow_id = str(uuid.uuid4())
    
    # Check if database exists
    db_path = get_data_dir() / "career_database.yaml"
    if not db_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Career database not found. Build database first."
        )
    
    # Start workflow in background
    background_tasks.add_task(
        run_document_generation_workflow,
        workflow_id,
        request.dict()
    )
    
    # Store workflow info
    active_workflows[workflow_id] = {
        "type": f"{request.document_type}_generation",
        "status": "started",
        "progress": 0,
        "started_at": datetime.utcnow()
    }
    
    return {
        "success": True,
        "workflow_id": workflow_id,
        "message": f"{request.document_type} generation started"
    }


async def run_document_generation_workflow(workflow_id: str, params: Dict[str, Any]):
    """Run document generation workflow."""
    try:
        # Implementation would follow similar pattern to job analysis
        # but generate CV or cover letter based on document_type
        pass
    except Exception as e:
        active_workflows[workflow_id]["status"] = "failed"
        active_workflows[workflow_id]["error"] = str(e)


# Workflow Management endpoints
@app.get("/api/workflows/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """Get workflow status."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    
    return WorkflowStatus(
        workflow_id=workflow_id,
        status=workflow["status"],
        progress=workflow.get("progress", 0),
        current_step=workflow.get("current_step", ""),
        result=workflow.get("result"),
        error=workflow.get("error")
    )


@app.get("/api/workflows")
async def list_workflows():
    """List all workflows."""
    workflows = []
    for wf_id, wf_data in active_workflows.items():
        workflows.append({
            "workflow_id": wf_id,
            "type": wf_data["type"],
            "status": wf_data["status"],
            "started_at": wf_data["started_at"],
            "progress": wf_data.get("progress", 0)
        })
    
    return {
        "workflows": workflows,
        "total": len(workflows)
    }


# File Upload endpoints
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document file."""
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt", ".md"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {allowed_extensions}"
        )
    
    # Save file
    upload_dir = get_upload_dir()
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}{file_ext}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "path": str(file_path)
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws/workflows/{workflow_id}")
async def websocket_workflow(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for workflow updates."""
    await websocket.accept()
    
    # Add to active connections
    if workflow_id not in active_connections:
        active_connections[workflow_id] = []
    active_connections[workflow_id].append(websocket)
    
    try:
        # Send current status
        if workflow_id in active_workflows:
            await websocket.send_json({
                "type": "status",
                "data": active_workflows[workflow_id]
            })
        
        # Keep connection alive
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        # Remove from active connections
        if workflow_id in active_connections:
            active_connections[workflow_id].remove(websocket)
            if not active_connections[workflow_id]:
                del active_connections[workflow_id]


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle value errors."""
    return {"error": str(exc)}, 400


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return {"error": "Internal server error", "detail": str(exc)}, 500


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )