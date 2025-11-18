"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
from pathlib import Path

from app.config import settings
from app.database import init_db, check_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered English tutoring platform with speech recognition and conversation practice",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration - Cho phép tất cả origins trong development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins (chỉ dùng development!)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Cho phép tất cả headers
    expose_headers=["*"],  # Expose tất cả headers cho client
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create directories
    Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize database
    try:
        init_db()
        if check_db_connection():
            logger.info("✅ Database connection successful")
        else:
            logger.error("❌ Database connection failed")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down application...")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_status = check_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": settings.APP_VERSION
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Include routers
from app.routers import auth

app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])

# Mount static files
static_path = Path("app/static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )    