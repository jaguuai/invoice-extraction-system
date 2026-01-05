"""
FastAPI Application
Main API entry point - Simplified with single process endpoint
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.logging import logger
from src.core.config import settings

# Single unified endpoint
from src.api.routes import process

app = FastAPI(
    title="Invoice Extraction API",
    description="AI-powered invoice extraction - Unified processing",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single endpoint
app.include_router(process.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Invoice Extraction API v2.0",
        "version": "2.0.0",
        "status": "running",
        "endpoint": "/api/v1/process"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.ENV
    }

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Invoice Extraction API v2.0 started")
    logger.info(f"Environment: {settings.ENV}")
    logger.info("📍 Single unified endpoint: POST /api/v1/process")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Invoice Extraction API stopped")
