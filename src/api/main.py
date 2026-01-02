"""
FastAPI Application
Main API entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.logging import logger
from src.core.config import settings

# Import routers
from src.api.routes import upload  # NEW!

app = FastAPI(
    title="Invoice Extraction API",
    description="AI-powered invoice extraction system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1")  # NEW!

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Invoice Extraction API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENV
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Invoice Extraction API started")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Invoice Extraction API stopped")