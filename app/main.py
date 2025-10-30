# # app/main.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import structlog
# from datetime import datetime
# from app.config import get_settings
# from app.api.v1.endpoints import router as api_router

# # Configure structured logging
# structlog.configure(
#     processors=[
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.JSONRenderer()
#     ]
# )

# logger = structlog.get_logger()
# settings = get_settings()

# # Create FastAPI app
# app = FastAPI(
#     title="DevAgent Swarm API",
#     description="AI-powered multi-agent system for code review automation",
#     version="1.0.0",
#     docs_url="/api/docs",
#     openapi_url="/api/openapi.json"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure properly in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include router
# app.include_router(api_router)

# @app.on_event("startup")
# async def startup_event():
#     """Run on application startup"""
#     logger.info("application_starting", environment=settings.environment)

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Run on application shutdown"""
#     logger.info("application_stopping")

# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "message": "Welcome to DevAgent Swarm API",
#         "version": "1.0.0",
#         "docs": "/api/docs"
#     }

# @app.get("/health")
# async def health_check():
#     """Health check endpoint for ECS/ALB"""
#     return {
#         "status": "healthy",
#         "timestamp": datetime.utcnow().isoformat(),
#         "version": "1.0.0",
#         "environment": settings.environment
#     }

# @app.get("/api/v1/status")
# async def api_status():
#     """API status with configuration info"""
#     return {
#         "api": "operational",
#         "aws_region": settings.aws_region,
#         "bedrock_configured": settings.bedrock_supervisor_agent_id is not None,
#         "github_configured": settings.github_token is not None,
#         "database": "connected" if settings.database_url else "not configured"
#     }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )

# app/main.py (Updated with GitHub Router Integration)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime
from app.config import get_settings
from app.api.v1.endpoints import router as api_router
from app.routers.github import router as github_router  # ✅ New: Import GitHub router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)


logger = structlog.get_logger()
settings = get_settings()


# Create FastAPI app
app = FastAPI(
    title="DevAgent Swarm API",
    description="AI-powered multi-agent system for code review automation",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(api_router)  # ✅ Existing API router (analyze/code, etc.)
app.include_router(github_router, prefix="/api/v1/github")  # ✅ New: GitHub webhook router


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("application_starting", environment=settings.environment)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("application_stopping")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DevAgent Swarm API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for ECS/ALB"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment
    }


@app.get("/api/v1/status")
async def api_status():
    """API status with configuration info"""
    return {
        "api": "operational",
        "aws_region": settings.aws_region,
        "bedrock_configured": settings.bedrock_supervisor_agent_id is not None,
        "github_configured": settings.github_token is not None,  # ✅ Updated: Check GitHub token
        "database": "connected" if settings.database_url else "not configured"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
