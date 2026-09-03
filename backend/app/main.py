"""app.main — FastAPI factory: CORS, error envelope, latency middleware."""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db
from .config import get_settings
from .routers.api import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setu.backend")

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SETU API",
        version=settings.algorithm_version,
        description="Matching and verification layer for corporate CSR in India.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_latency(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Latency-Ms"] = f"{(time.perf_counter() - t0) * 1000:.1f}"
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={
            "error": {
                "code": "INTERNAL",
                "message": "Internal server error — see server logs.",
                "detail": {"path": request.url.path},
            }
        })

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request failed validation.",
                "detail": exc.errors()[:5],
            }
        })

    app.include_router(router)

    @app.on_event("startup")
    def _startup() -> None:
        db.connect()  # create tables
        try:
            rows = db.list_ngos()
            logger.info("db ready — %d ngos", len(rows))
        except Exception:
            logger.warning("db not seeded yet — run python -m seed --reset")

    return app


app = create_app()
