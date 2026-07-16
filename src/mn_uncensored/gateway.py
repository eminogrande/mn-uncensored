from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.background import BackgroundTask
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .security import token_key


MAX_REQUEST_BYTES = 16 * 1024 * 1024
FORWARDED_REQUEST_HEADERS = {"accept", "content-type", "user-agent"}
FORWARDED_RESPONSE_HEADERS = {
    "cache-control",
    "content-type",
    "retry-after",
    "x-request-id",
}


def error_payload(message: str, error_type: str, code: str) -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": error_type,
            "param": None,
            "code": code,
        }
    }


async def state_get(state: Any, key: str, default: Any = None) -> Any:
    return await asyncio.to_thread(state.get, key, default)


def create_app(
    *,
    state: Any,
    backend_url: str,
    model: str,
    proxy_key: str,
    proxy_secret: str,
) -> FastAPI:
    app = FastAPI(
        title="MN Uncensored",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.modal.run", "*.modal.direct", "testserver"],
    )
    bearer = HTTPBearer(auto_error=False)

    @app.exception_handler(HTTPException)
    async def openai_http_error(_request: Request, error: HTTPException) -> JSONResponse:
        if isinstance(error.detail, dict) and {"message", "type", "code"} <= error.detail.keys():
            content = {"error": error.detail}
        else:
            content = error_payload(
                str(error.detail),
                "invalid_request_error",
                "http_error",
            )
        return JSONResponse(
            status_code=error.status_code,
            content=content,
            headers=error.headers,
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Any:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content=error_payload(
                            "Request body is too large.",
                            "invalid_request_error",
                            "request_too_large",
                        ),
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_payload(
                        "Invalid Content-Length header.",
                        "invalid_request_error",
                        "invalid_content_length",
                    ),
                )

        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    async def authenticate(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> dict[str, Any]:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_payload(
                    "A Bearer API token is required.",
                    "authentication_error",
                    "missing_api_token",
                )["error"],
                headers={"WWW-Authenticate": "Bearer"},
            )

        metadata = await state_get(state, token_key(credentials.credentials))
        if not metadata or not metadata.get("active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_payload(
                    "The API token is invalid or revoked.",
                    "authentication_error",
                    "invalid_api_token",
                )["error"],
                headers={"WWW-Authenticate": "Bearer"},
            )
        return metadata

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/status", dependencies=[Depends(authenticate)])
    async def model_status() -> dict[str, Any]:
        desired_state = await state_get(state, "desired_state", "stopped")
        return {
            "model": model,
            "state": desired_state,
            "ready": desired_state == "started",
        }

    @app.get("/v1/models", dependencies=[Depends(authenticate)])
    async def models() -> dict[str, Any]:
        return {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "mn",
                }
            ],
        }

    async def close_upstream(
        response: httpx.Response,
        client: httpx.AsyncClient,
    ) -> None:
        await response.aclose()
        await client.aclose()

    async def stream_upstream(response: httpx.Response) -> AsyncIterator[bytes]:
        async for chunk in response.aiter_raw():
            yield chunk

    @app.api_route(
        "/v1/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        dependencies=[Depends(authenticate)],
    )
    async def proxy(path: str, request: Request) -> StreamingResponse:
        desired_state = await state_get(state, "desired_state", "stopped")
        if desired_state != "started":
            state_message = {
                "starting": "MN Uncensored is still starting.",
                "stopping": "MN Uncensored is stopping.",
                "stopped": "MN Uncensored is stopped. Run `mn start`.",
            }.get(desired_state, "MN Uncensored is unavailable.")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=error_payload(
                    state_message,
                    "service_unavailable",
                    f"model_{desired_state}",
                ),
                headers={"Retry-After": "15"},
            )

        body = await request.body()
        if len(body) > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content=error_payload(
                    "Request body is too large.",
                    "invalid_request_error",
                    "request_too_large",
                ),
            )

        content_type = request.headers.get("content-type", "")
        if body and "application/json" in content_type:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_payload(
                        "The request body is not valid JSON.",
                        "invalid_request_error",
                        "invalid_json",
                    ),
                )
            if isinstance(payload, dict) and "model" in payload:
                payload["model"] = model
                body = json.dumps(payload, separators=(",", ":")).encode()

        request_id = request.headers.get("x-request-id") or f"mn_{uuid.uuid4().hex}"
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() in FORWARDED_REQUEST_HEADERS
        }
        headers.update(
            {
                "Modal-Key": proxy_key,
                "Modal-Secret": proxy_secret,
                "X-Request-ID": request_id,
            }
        )

        client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=30, read=3600, write=60, pool=30),
            follow_redirects=False,
        )
        upstream_request = client.build_request(
            request.method,
            f"{backend_url}/v1/{path}",
            params=request.query_params,
            headers=headers,
            content=body,
        )
        try:
            upstream = await client.send(upstream_request, stream=True)
        except httpx.HTTPError:
            await client.aclose()
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content=error_payload(
                    "The model backend could not be reached.",
                    "api_connection_error",
                    "backend_unreachable",
                ),
            )

        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() in FORWARDED_RESPONSE_HEADERS
        }
        response_headers.setdefault("X-Request-ID", request_id)
        return StreamingResponse(
            stream_upstream(upstream),
            status_code=upstream.status_code,
            headers=response_headers,
            background=BackgroundTask(close_upstream, upstream, client),
        )

    return app
