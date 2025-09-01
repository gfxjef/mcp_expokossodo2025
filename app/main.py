"""
MCP-Expokossodo Main Application
FastAPI server for MCP tools related to Expokossodo events
"""
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from app.config import settings
from app.logging import setup_logging
from app.auth import auth_middleware
from app.api.tools import router as tools_router
from app.cache.redis_client import init_cache, close_cache

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="MCP tools for Expokossodo event management",
    debug=settings.debug
)


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("application_starting", version=settings.app_version)
    # Initialize cache
    await init_cache()
    logger.info("application_started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("application_shutting_down")
    # Close cache connection
    await close_cache()
    logger.info("application_shutdown_complete")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Add request logging and tracing"""
    trace_id = str(uuid.uuid4())
    
    # Add trace ID to request state
    request.state.trace_id = trace_id
    
    start_time = time.time()
    
    # Log request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        trace_id=trace_id,
        user_agent=request.headers.get("user-agent"),
        client_ip=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
        trace_id=trace_id
    )
    
    # Add trace ID to response headers
    response.headers["X-Trace-ID"] = trace_id
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    
    logger.error(
        "unhandled_exception",
        exception=str(exc),
        exception_type=exc.__class__.__name__,
        trace_id=trace_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "trace_id": trace_id
        },
        headers={"X-Trace-ID": trace_id}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


# MCP Tools router
app.include_router(
    tools_router,
    prefix="/mcp/tools",
    tags=["MCP Tools"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "tools_endpoint": "/mcp/tools",
        "health_endpoint": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )