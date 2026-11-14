from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="AI-powered Fashion Discovery Platform",
    version=settings.APP_VERSION,
)

# Configure CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root welcome endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }


# Register central API router under /api/v1
app.include_router(api_router, prefix="/api/v1")
