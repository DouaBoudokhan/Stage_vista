"""
StockIT Backend API
FastAPI application for inventory management
"""
import sys

# Reconfigure stdout and stderr for UTF-8 on Windows to prevent UnicodeEncodeError with emojis
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .routers import auth, stock_entry, document_analysis, products, labels, inventory

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for StockIT Mobile Inventory Management",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"📊 Initializing database...")
    try:
        init_db()
        print(f"✅ Database initialization completed successfully")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")


# Health check
@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "StockIT API is running",
        "version": settings.VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected",
        "ai_services": "enabled"
    }


# Include routers (supported under both /api/v1 and root prefix for API client compatibility)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(document_analysis.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX) 
app.include_router(labels.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory.router, prefix=settings.API_V1_PREFIX)

# Also register without prefix for direct access
app.include_router(auth.router, prefix="")
app.include_router(document_analysis.router, prefix="")
app.include_router(products.router, prefix="")
app.include_router(labels.router, prefix="")
app.include_router(inventory.router, prefix="")

# app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
# app.include_router(stock_entry.router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        reload_dirs=["app"] if settings.DEBUG else None
    )
