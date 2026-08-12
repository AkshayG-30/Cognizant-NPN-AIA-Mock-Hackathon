"""
CarePath AI — FastAPI Application
"Finding the Right Specialist. Faster. Fairer."

Main application entry point. Initializes:
  - CORS middleware
  - Structured logging
  - Exception handlers
  - ML model loading
  - Database connection
  - API route mounting
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import CarePathError, carepath_exception_handler, generic_exception_handler
from app.core.logging import get_logger, request_id_ctx, setup_logging
from app.db.database import close_db, init_db
from app.ml.model_registry import get_model_registry

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # Startup
    setup_logging(
        log_level=settings.log_level,
        json_output=settings.is_production,
    )
    logger.info(
        "starting",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )

    # Initialize database
    init_db()
    from app.db.database import create_tables
    await create_tables()
    logger.info("database_initialized")

    # Load ML model
    registry = get_model_registry()
    if registry.load_wait_time_model():
        logger.info("ml_model_ready", model="wait_time", version=settings.wait_model_version)
    else:
        logger.warning("ml_model_not_loaded — prediction endpoints will return 503")

    yield

    # Shutdown
    await close_db()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="CarePath AI",
        description=(
            "Clinical Decision Support API for specialty referral orchestration.\n\n"
            "**Finding the Right Specialist. Faster. Fairer.**\n\n"
            "Features:\n"
            "- Queue-theory-augmented wait-time prediction (LightGBM)\n"
            "- Multi-objective provider optimization (OR-Tools)\n"
            "- FHIR R4-compatible referral mapping\n"
            "- Evidence-grounded clinical explanations\n"
            "- Fairness-aware provider ranking\n\n"
            "⚠️ This is a research prototype. Not certified for clinical use."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(CarePathError, carepath_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request_id_ctx.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    # Mount API routes
    prefix = settings.api_prefix

    from app.api.v1.health import router as health_router
    from app.api.v1.auth import router as auth_router
    from app.api.v1.providers import router as providers_router
    from app.api.v1.referrals import router as referrals_router
    from app.api.v1.predictions import router as predictions_router
    from app.api.v1.recommendations import router as recommendations_router
    from app.api.v1.fhir import router as fhir_router
    from app.api.v1.appointments import router as appointments_router
    from app.api.v1.models import router as models_router
    from app.api.v1.monitoring import router as monitoring_router
    from app.api.v1.reports import router as reports_router
    from app.api.v1.ai import router as ai_router
    from app.api.v1.carepath import router as carepath_router
    from app.api.v1.specialties import router as specialties_router
    from app.api.v1.doctors import router as doctors_router
    from app.api.v1.hospitals import router as hospitals_router
    from app.api.v1.doctor import router as doctor_router
    from app.api.v1.messages import router as messages_router
    from app.api.v1.notifications import router as notifications_router
    from app.api.v1.admin import router as admin_router

    app.include_router(health_router, prefix=prefix)
    app.include_router(auth_router, prefix=prefix)
    app.include_router(providers_router, prefix=prefix)
    app.include_router(referrals_router, prefix=prefix)
    app.include_router(predictions_router, prefix=prefix)
    app.include_router(recommendations_router, prefix=prefix)
    app.include_router(fhir_router, prefix=prefix)
    app.include_router(appointments_router, prefix=prefix)
    app.include_router(models_router, prefix=prefix)
    app.include_router(monitoring_router, prefix=prefix)
    app.include_router(reports_router, prefix=prefix)
    app.include_router(ai_router, prefix=prefix)
    app.include_router(carepath_router, prefix=prefix)
    app.include_router(specialties_router, prefix=prefix)
    app.include_router(doctors_router, prefix=prefix)
    app.include_router(hospitals_router, prefix=prefix)
    app.include_router(doctor_router, prefix=prefix)
    app.include_router(messages_router, prefix=prefix)
    app.include_router(notifications_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)

    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    frontend_dir = settings.resolve_path("../frontend")
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

        @app.get("/", include_in_schema=False)
        @app.get("/ui", include_in_schema=False)
        async def serve_ui():
            return FileResponse(str(frontend_dir / "index.html"))
    else:
        @app.get("/", include_in_schema=False)
        async def root():
            return {
                "service": "CarePath AI",
                "tagline": "Finding the Right Specialist. Faster. Fairer.",
                "version": settings.app_version,
                "docs": "/docs",
                "health": f"{prefix}/health",
            }

    return app


app = create_app()
