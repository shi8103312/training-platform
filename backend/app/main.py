"""
FastAPI Application Entry Point
"""
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .database import init_db
from .redis import close_redis


def seed_if_empty():
    """Seed database with initial data if tables are empty."""
    import sys
    from pathlib import Path
    from .database import SessionLocal
    from .models.user import User
    try:
        db = SessionLocal()
        count = db.query(User).count()
        db.close()
        if count == 0:
            print("Database is empty, seeding initial data...")
            # Import seed_data from backend root (parent of app/)
            seed_data_path = Path(__file__).parent.parent / "seed_data"
            import importlib.util
            spec = importlib.util.spec_from_file_location("seed_data", seed_data_path.with_suffix(".py"))
            seed_data = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(seed_data)
            seed_data.seed_database()
    except Exception as e:
        print(f"Seed check failed (may be normal on first run): {e}")

from .api.v1 import auth, user, department, training, material, progress, exam, comment, notification, system_settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.APP_NAME}...")

    # Initialize database tables
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

    # Seed initial data if database is empty
    seed_if_empty()

    yield

    # Shutdown
    print("Shutting down...")
    await close_redis()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="集团内部员工培训平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter

# Mount uploads directory for static file serving
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 90002,
            "message": "服务器内部错误",
        },
    )


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(user.router, prefix=settings.API_V1_PREFIX)
app.include_router(department.router, prefix=settings.API_V1_PREFIX)
app.include_router(training.router, prefix=settings.API_V1_PREFIX)
app.include_router(material.router, prefix=settings.API_V1_PREFIX)
app.include_router(progress.router, prefix=settings.API_V1_PREFIX)
app.include_router(exam.router, prefix=settings.API_V1_PREFIX)
app.include_router(comment.router, prefix=settings.API_V1_PREFIX)
app.include_router(notification.router, prefix=settings.API_V1_PREFIX)
app.include_router(system_settings.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }


@app.get("/debug/uploads")
async def debug_uploads():
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    return {
        "uploads_dir": uploads_dir,
        "exists": os.path.exists(uploads_dir),
        "files": os.listdir(uploads_dir) if os.path.exists(uploads_dir) else [],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )