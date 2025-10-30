# app/api/v1/endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import time
import uuid
import structlog
from app.models import (
    AnalyzeCodeRequest,
    AnalyzePRRequest,
    AnalyzeResponse
)
from app.core.analyzer import CodeAnalyzer

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Initialize analyzer (singleton)
analyzer = CodeAnalyzer()

@router.post("/analyze/code", response_model=AnalyzeResponse)
async def analyze_code(request: AnalyzeCodeRequest):
    """
    Analyze code snippet for security, performance, and quality issues
    
    Args:
        request: Code analysis request with code and language
    
    Returns:
        AnalyzeResponse with issues, suggestions, and metrics
    """
    start_time = time.time()
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    
    logger.info(
        "analyze_code_request",
        request_id=request_id,
        language=request.language,
        code_length=len(request.code)
    )
    
    try:
        # Perform analysis
        result = await analyzer.analyze_code(
            code=request.code,
            language=request.language,
            filename=request.filename
        )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = AnalyzeResponse(
            request_id=request_id,
            status="completed",
            execution_time_ms=execution_time_ms,
            timestamp=datetime.utcnow(),
            results={
                "code_review": result.dict()
            }
        )
        
        logger.info(
            "analyze_code_success",
            request_id=request_id,
            issues_found=len(result.issues),
            execution_time_ms=execution_time_ms
        )
        
        return response
    
    except Exception as e:
        logger.error(
            "analyze_code_failed",
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/analyze/pr", response_model=AnalyzeResponse)
async def analyze_pr(request: AnalyzePRRequest):
    """
    Analyze GitHub Pull Request
    
    Args:
        request: PR analysis request with repository and PR number
    
    Returns:
        AnalyzeResponse with complete review
    """
    # TODO: Implement GitHub integration
    raise HTTPException(
        status_code=501,
        detail="PR analysis coming soon! Use /analyze/code for now."
    )
