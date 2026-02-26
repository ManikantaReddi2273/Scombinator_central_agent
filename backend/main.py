"""
Main FastAPI application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from config import settings
from routers import auth, companies, emails, drafts, dashboard, outbound
import traceback

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="S Combinator Central Agent Platform - Multi-company AI agent for Customer Acquisition and Hiring"
)

# CORS middleware - MUST be added before routers
# Note: allow_credentials=True cannot be used with allow_origins=["*"]
# For development, we allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Exception handlers to ensure CORS headers are always sent
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers"""
    origin = request.headers.get("origin", "http://localhost:3000")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": origin if origin in [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ] else "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions with CORS headers"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    origin = request.headers.get("origin", "http://localhost:3000")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": origin if origin in [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ] else "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Handle OPTIONS requests for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle CORS preflight OPTIONS requests"""
    origin = request.headers.get("origin", "http://localhost:3000")
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": origin if origin in [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ] else "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

# Startup: log whether n8n API key is configured (for Update CRM auth)
@app.on_event("startup")
async def startup_event():
    import logging
    logger = logging.getLogger(__name__)
    if settings.N8N_SERVICE_API_KEY:
        logger.info("N8N_SERVICE_API_KEY is set (Update CRM / n8n auth enabled)")
    else:
        logger.warning("N8N_SERVICE_API_KEY is not set; Update CRM endpoint will require Bearer JWT")

# Include routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(emails.router)
app.include_router(drafts.router)
app.include_router(dashboard.router)
app.include_router(outbound.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "S Combinator Central Agent Platform API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - doesn't require database"""
    return {"status": "healthy"}


@app.get("/health/cors")
async def health_check_cors():
    """CORS test endpoint"""
    return {
        "status": "healthy",
        "cors": "enabled",
        "message": "If you can see this, CORS is working!"
    }


@app.get("/health/db")
async def health_check_db():
    """Health check endpoint with database connection test"""
    try:
        from database import async_engine
        from sqlalchemy import text
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

