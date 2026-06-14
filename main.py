import asyncio
import logging
import os
from dotenv import load_dotenv
from utils.logging import configure_logging


load_dotenv()

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from api.routes import router
from core.browser import browser_manager
from core.queue import solver_queue
from middleware.auth import ApiKeyAuthMiddleware


_browser_restart_task: asyncio.Task | None = None


# Configure logging from environment variable `LOG_LEVEL`
_env_level = os.getenv("LOG_LEVEL")
if _env_level:
    level = getattr(logging, _env_level.upper(), logging.INFO)
else:
    level = logging.INFO

# Initialize colored logging via utils.logging
configure_logging(level=level)

app = FastAPI(title="Turnstile Solver")
app.add_middleware(ApiKeyAuthMiddleware)
app.include_router(router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "x-api-key",
        "description": "Required for /api/* requests. x-api-keys is also accepted.",
    }

    for path, methods in openapi_schema.get("paths", {}).items():
        if not path.startswith("/api/"):
            continue
        for operation in methods.values():
            operation["security"] = [{"ApiKeyAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


async def _browser_restart_loop(interval: int) -> None:
    logger = logging.getLogger(__name__)
    while True:
        await asyncio.sleep(interval)
        logger.info("Browser restart interval reached (%ds), restarting...", interval)
        await browser_manager.restart()


@app.on_event("startup")
async def startup() -> None:
    logger = logging.getLogger(__name__)
    logger.info("Application startup: initializing browser and worker")
    await browser_manager.start()
    solver_queue.start_worker()

    interval = int(os.getenv("BROWSER_RESTART_INTERVAL", "7200"))
    global _browser_restart_task
    _browser_restart_task = asyncio.create_task(_browser_restart_loop(interval))
    logger.info("Browser restart task started (interval=%ds)", interval)


@app.on_event("shutdown")
async def shutdown() -> None:
    logger = logging.getLogger(__name__)
    logger.info("Application shutdown: stopping worker and browser")

    if _browser_restart_task:
        _browser_restart_task.cancel()
        try:
            await _browser_restart_task
        except asyncio.CancelledError:
            pass

    await solver_queue.stop_worker()
    await browser_manager.stop()