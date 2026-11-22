import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.message_routes import router as message_router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("whatsapp_bot")

settings = get_settings()

app = FastAPI(
    title="WhatsApp Admin Notification Bot API",
    description=(
        "FastAPI backend for manually sending vehicle compliance notifications "
        "(Insurance, PUCC, Fitness) using Meta WhatsApp Cloud API."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(message_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status and Meta API configuration mode."""
    return {
        "status": "healthy",
        "app_env": settings.app_env,
        "dry_run_active": not settings.is_configured_for_live,
        "whatsapp_configured": settings.is_configured_for_live,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.app_env == "development"),
    )
