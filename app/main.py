import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.errors import AppError

from app.api.health import router as health_router
from app.api.health import router as health_router
from app.api.tools import router as tools_router
from app.api.executions import router as executions_router
from app.db import get_engine
from app.logging import setup_logging
from app.migrations import run_migrations
from app.settings import settings
from app.trace import ensure_trace_id

logger = logging.getLogger("cto")


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    await run_migrations(engine)
    logger.info("startup_complete", extra={"env": settings.environment})
    yield
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        trace_id = request.headers.get("x-trace-id") or ""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error,
                "message": exc.message,
                "trace_id": trace_id,
            },
            headers={"x-trace-id": trace_id} if trace_id else None,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        trace_id = request.headers.get("x-trace-id") or ""
        return JSONResponse(
            status_code=422,
            content={
                "error": "request_validation_error",
                "message": "request payload validation failed",
                "trace_id": trace_id,
            },
            headers={"x-trace-id": trace_id} if trace_id else None,
        )

    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        incoming = request.headers.get("x-trace-id")
        trace_id = ensure_trace_id(incoming)

        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled_error", extra={"path": request.url.path, "trace_id": trace_id}
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "an unexpected internal error occurred",
                    "trace_id": trace_id,
                    },
                headers={"x-trace-id": trace_id},
            )

        response.headers["x-trace-id"] = trace_id
        return response

    app.include_router(health_router)
    app.include_router(tools_router)
    app.include_router(executions_router)
    return app


app = create_app()
