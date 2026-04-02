from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, location, events, emergency_contacts, status as device_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application."""
    # Run simple dev metadata creation (Note: Replace with alembic in production)
    await init_db()
    yield
    # Any teardown code (like closing redis pools) goes here


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Smart Safety Wearable",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Global exception handler to guarantee consistent JSON error format
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later.", "success": False, "error": str(exc)},
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Routers
app.include_router(auth.router)
app.include_router(location.router)
app.include_router(events.router)
app.include_router(emergency_contacts.router)
app.include_router(device_status.router)


@app.get("/", tags=["Health"])
async def root():
    """Information about the application."""
    return {"app": settings.APP_NAME, "version": "1.0.0", "status": "running"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple healthcheck endpoint."""
    return {"status": "healthy"}
