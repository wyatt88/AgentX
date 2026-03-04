"""
AgentX Backend — FastAPI Application Entry Point

Responsibilities:
  - Create the FastAPI application instance
  - Configure CORS middleware
  - Register global exception handlers
  - Mount all API routers
"""

import logging
import traceback
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Existing routers ──────────────────────────────────────────────────────────
from .routers import agent
from .routers import mcp
from .routers import chat_record
from .routers import schedule

# ── New routers (2.0) ─────────────────────────────────────────────────────────
# Wrapped in try/except so the app still boots even if an engineer hasn't
# pushed their router module yet.
try:
    from .routers import workflow as workflow_router
except ImportError:
    workflow_router = None

try:
    from .routers import model as model_router
except ImportError:
    model_router = None

# ── Logging ───────────────────────────────────────────────────────────────────
logger = logging.getLogger("agentx")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AgentX API",
    description="Enterprise AI Agent Management Platform",
    version="2.0.0",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
# Allow the React frontend (dev: localhost:3000/5173, prod: custom domain)
cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Accel-Buffering"],
)

# ── Global Exception Handlers ────────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 422 validation errors in a consistent format."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standard HTTP error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors — log full traceback, return 500."""
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ── URL Prefix ────────────────────────────────────────────────────────────────
# Read APP_ENV environment variable and set URL prefix accordingly
app_env = os.environ.get("APP_ENV", "")
url_prefix = "/api" if app_env == "production" else ""

# ── Router Registration ──────────────────────────────────────────────────────
app.include_router(agent.router, prefix=url_prefix)
app.include_router(mcp.router, prefix=url_prefix)
app.include_router(chat_record.router, prefix=url_prefix)
app.include_router(schedule.router, prefix=url_prefix)

if workflow_router is not None:
    app.include_router(workflow_router.router, prefix=url_prefix)
    logger.info("Registered workflow router")

if model_router is not None:
    app.include_router(model_router.router, prefix=url_prefix)
    logger.info("Registered model router")


# ── Health Check ──────────────────────────────────────────────────────────────


@app.get("/")
def home():
    return {"App": "AgentX-BE", "version": "2.0.0"}


@app.get("/health")
def health():
    """Lightweight health-check endpoint for ALB / ECS."""
    return {"status": "ok"}
