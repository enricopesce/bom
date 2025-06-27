import os
import sys
import uuid
import shutil
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import our VM assessment modules (now in web_app)
from processors.factory import ProcessorFactory
from pricing.oracle_cloud_pricing import OracleCloudPricingCalculator
from reports.report_generators import (
    CSVReportGenerator, 
    ExcelReportGenerator, 
    TextReportGenerator, 
    JSONReportGenerator,
    SalesExcelReportGenerator
)

app = FastAPI(
    title="VM Assessment BOM Generator",
    description="Web-based tool for generating Bill of Materials from VM assessment files",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return await request_validation_exception_handler(request, exc)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Global storage for processing sessions
processing_sessions = {}

class ProcessingSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = "pending"
        self.progress = 0
        self.message = "Waiting to start..."
        self.created_at = datetime.now()
        self.output_dir = None
        self.files = []
        self.error = None

# Cleanup old sessions and files
async def cleanup_old_sessions():
    cutoff_time = datetime.now() - timedelta(hours=24)
    expired_sessions = []
    
    for session_id, session in processing_sessions.items():
        if session.created_at < cutoff_time:
            expired_sessions.append(session_id)
            # Cleanup files
            if session.output_dir and os.path.exists(session.output_dir):
                shutil.rmtree(session.output_dir, ignore_errors=True)
    
    for session_id in expired_sessions:
        del processing_sessions[session_id]

@app.on_event("startup")
async def startup_event():
    # Create uploads directory if it doesn't exist
    os.makedirs("static/uploads", exist_ok=True)
    # Schedule periodic cleanup
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)  # Cleanup every hour
        await cleanup_old_sessions()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("simple.html", {"request": request})

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None)
):
    logger.info(f"Upload request received - File: {getattr(file, 'filename', 'NO_FILENAME') if file else 'NO_FILE'}, Size: {getattr(file, 'size', 'NO_SIZE') if file else 'NO_FILE'}")
    
    try:
        # Validate parameters
        if not file:
            logger.error("No file provided in request")
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file
        allowed_extensions = ('.zip', '.xls', '.xlsx')
        if not file.filename or not file.filename.lower().endswith(allowed_extensions):
            logger.error(f"Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only ZIP, XLS, or XLSX files are allowed")
        
        # Read file content to check size
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(content) > 100 * 1024 * 1024:  # 100MB limit
            logger.error(f"File too large: {len(content)} bytes")
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
            
        logger.info(f"File validation passed - {file.filename} ({len(content)} bytes)")
        
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")
    
    # Create session
    session_id = str(uuid.uuid4())
    session = ProcessingSession(session_id)
    processing_sessions[session_id] = session
    
    # Save uploaded file
    upload_dir = f"static/uploads/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    logger.info(f"File saved to: {file_path}")
    
    # Start background processing
    background_tasks.add_task(
        process_vm_assessment, 
        session_id, 
        file_path
    )
    
    return {"session_id": session_id, "status": "started"}

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    response_data = {
        "status": session.status,
        "progress": session.progress,
        "message": session.message,
        "files": session.files,
        "error": session.error
    }
    
    # Include summary if available and merge into response
    if hasattr(session, 'summary') and session.summary:
        response_data.update(session.summary)
    
    return response_data

@app.get("/admin/sessions")
async def get_all_sessions():
    """Admin endpoint to view all active sessions"""
    sessions_info = []
    for session_id, session in processing_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "status": session.status,
            "progress": session.progress,
            "created_at": session.created_at.isoformat(),
            "files_count": len(session.files),
            "has_error": session.error is not None
        })
    
    return {
        "total_sessions": len(sessions_info),
        "sessions": sessions_info
    }

@app.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    if not session.output_dir:
        raise HTTPException(status_code=404, detail="No files available")
    
    file_path = os.path.join(session.output_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

async def process_vm_assessment(session_id: str, file_path: str):
    session = processing_sessions[session_id]
    logger.info(f"Starting background processing for session {session_id}")
    
    try:
        session.status = "processing"
        session.message = "Starting VM assessment..."
        session.progress = 10
        
        # Import VM assessment modules
        from processors.factory import ProcessorFactory
        from simple_reports import SimplifiedReportGenerator
        
        session.message = "Processing VM data..."
        session.progress = 30
        
        # Create processor factory and process the file
        processor_factory = ProcessorFactory()
        processor = processor_factory.create_processor(file_path)
        assessment = processor.extract_vm_data()
        session.progress = 50
        
        session.message = "Calculating pricing..."
        # Calculate pricing
        pricing_calculator = OracleCloudPricingCalculator('pricing.json')
        bom = pricing_calculator.calculate_assessment_cost(assessment)
        session.progress = 70
        
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"static/uploads/{session_id}/reports_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        session.output_dir = output_dir
        
        session.message = "Generating reports..."
        session.progress = 80
        
        # Generate all three optimized reports
        report_generator = SimplifiedReportGenerator(output_dir)
        generated_files = report_generator.generate_all_reports(bom)
        
        session.files = list(generated_files.values())
        session.progress = 100
        session.status = "completed"
        session.message = f"Successfully generated {len(generated_files)} report files"
        
        # Calculate summary stats for frontend
        total_cost = bom.total_monthly_cost if bom else 0
        session.summary = {
            'total_vms': len(assessment.vms),
            'powered_on_vms': len([vm for vm in assessment.vms if vm.is_powered_on]),
            'total_cost': f"{total_cost:.2f}",
            'formats_generated': len(generated_files)
        }
        
    except Exception as e:
        logger.error(f"Processing error for session {session_id}: {str(e)}", exc_info=True)
        session.status = "error"
        session.error = str(e)
        session.message = f"Error: {str(e)}"
        session.progress = 0

@app.get("/processing/{session_id}", response_class=HTMLResponse)
async def processing_page(request: Request, session_id: str):
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return templates.TemplateResponse(
        "processing.html", 
        {"request": request, "session_id": session_id}
    )

@app.get("/results/{session_id}", response_class=HTMLResponse)
async def results_page(request: Request, session_id: str):
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    if session.status != "completed":
        # Redirect to processing page if not completed
        return templates.TemplateResponse(
            "processing.html", 
            {"request": request, "session_id": session_id}
        )
    
    return templates.TemplateResponse(
        "results.html", 
        {"request": request, "session_id": session_id}
    )

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    if workers > 1:
        # Use Gunicorn for multiple workers in production
        import subprocess
        import sys
        
        cmd = [
            sys.executable, "-m", "gunicorn",
            "app:app",
            "-w", str(workers),
            "-k", "uvicorn.workers.UvicornWorker",
            "-b", f"{host}:{port}",
            "--log-level", log_level,
            "--access-logfile", "-",
            "--error-logfile", "-"
        ]
        subprocess.run(cmd)
    else:
        # Development mode with single worker
        uvicorn.run(app, host=host, port=port, log_level=log_level)