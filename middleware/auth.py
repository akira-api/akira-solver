import os
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        expected_api_key = os.getenv("API_KEY")
        if not expected_api_key:
            return JSONResponse(
                status_code=500,
                content={"detail": "API key is not configured"},
            )

        provided_api_key = request.headers.get("x-api-key") or request.headers.get("x-api-keys")
        if not provided_api_key or not secrets.compare_digest(provided_api_key, expected_api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
