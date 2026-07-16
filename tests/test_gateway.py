from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from mn_uncensored import gateway
from mn_uncensored.gateway import create_app
from mn_uncensored.security import token_key


TOKEN = "sk-mn-test-token"
MODELS: dict[str, dict[str, Any]] = {
    "god": {
        "aliases": ["nuri/ornith-397b-abliterated"],
        "backend_url": "https://god.backend.example",
        "context_window": 262144,
        "lifecycle_key": "model:god:lifecycle",
        "max_output_tokens": 32768,
        "model": "mn/god",
    },
    "code": {
        "aliases": ["ornith-code"],
        "backend_url": "https://code.backend.example",
        "context_window": 131072,
        "lifecycle_key": "model:code:lifecycle",
        "max_output_tokens": 16384,
        "model": "mn/code",
    },
    "fast": {
        "aliases": [],
        "backend_url": "https://fast.backend.example",
        "context_window": 65536,
        "lifecycle_key": "model:fast:lifecycle",
        "max_output_tokens": 8192,
        "model": "mn/fast",
    },
}


class FakeState:
    def __init__(self, values: dict[str, object] | None = None) -> None:
        self.values = values or {}

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)


def lifecycle(desired_state: str, updated_at: str = "2026-07-16T12:00:00Z") -> dict[str, object]:
    return {
        "schema": 1,
        "desired_state": desired_state,
        "updated_at": updated_at,
    }


def state_values(**model_states: str) -> dict[str, object]:
    values: dict[str, object] = {
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    for key, desired_state in model_states.items():
        values[MODELS[key]["lifecycle_key"]] = lifecycle(desired_state)
    return values


def client_for(
    values: dict[str, object],
    *,
    state: FakeState | None = None,
) -> TestClient:
    app = create_app(
        state=state or FakeState(values),
        models=MODELS,
        default_model="god",
        proxy_key="proxy-key",
        proxy_secret="proxy-secret",
    )
    return TestClient(app)


def auth_headers(**extra: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}", **extra}


def test_health_is_public() -> None:
    with client_for({}) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_models_requires_bearer_token() -> None:
    with client_for({}) as client:
        response = client.get("/v1/models")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_api_token"


def test_authentication_precedes_model_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BackendMustNotStart:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("unauthenticated traffic must not reach a backend")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackendMustNotStart)
    with client_for({}) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "mn/does-not-exist", "messages": []},
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_api_token"


def test_models_list_all_catalog_entries_without_waking_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BackendMustNotStart:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("listing models must not create an upstream client")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackendMustNotStart)
    with client_for(state_values(god="stopped", code="stopped", fast="stopped")) as client:
        response = client.get("/v1/models", headers=auth_headers())

    assert response.status_code == 200
    data = response.json()["data"]
    assert [entry["id"] for entry in data] == ["mn/god", "mn/code", "mn/fast"]
    assert {
        entry["id"]: (
            entry["context_length"],
            entry["max_output_tokens"],
        )
        for entry in data
    } == {
        "mn/god": (262144, 32768),
        "mn/code": (131072, 16384),
        "mn/fast": (65536, 8192),
    }


def test_status_reports_isolated_model_lifecycles() -> None:
    values = state_values(god="auto", code="stopped", fast="started")
    with client_for(values) as client:
        all_response = client.get("/status", headers=auth_headers())
        code_response = client.get(
            "/status",
            headers=auth_headers(),
            params={"model": "mn/code"},
        )

    assert all_response.status_code == 200
    assert {
        entry["model"]: entry["state"]
        for entry in all_response.json()["data"]
    } == {
        "mn/god": "auto",
        "mn/code": "stopped",
        "mn/fast": "started",
    }
    assert code_response.json() == {
        "model": "mn/code",
        "state": "stopped",
        "updated_at": "2026-07-16T12:00:00Z",
        "ready": None,
    }


def test_default_model_uses_legacy_lifecycle_during_migration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RecordingSuccessClient.reset()
    monkeypatch.setattr(gateway.httpx, "AsyncClient", RecordingSuccessClient)
    values = {
        "desired_state": "started",
        "state_updated_at": "legacy-time",
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"messages": []},
        )

    assert response.status_code == 200
    assert RecordingSuccessClient.urls == [
        "https://god.backend.example/v1/chat/completions"
    ]
    assert json.loads(RecordingSuccessClient.bodies[0])["model"] == "mn/god"


def test_stopped_model_returns_structured_503_without_backend_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BackendMustNotStart:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("stopped mode must not create an upstream client")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackendMustNotStart)
    values = state_values(god="auto", code="stopped", fast="auto")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "mn/code", "messages": []},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_stopped"
    assert "mn/code" in response.json()["error"]["message"]
    assert response.headers["retry-after"] == "15"


def test_revoked_token_is_rejected() -> None:
    values = {
        token_key(TOKEN): {"active": False, "name": "revoked"},
    }
    with client_for(values) as client:
        response = client.get(
            "/status",
            headers=auth_headers(),
            params={"model": "mn/fast"},
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_api_token"


def test_unknown_and_non_string_models_fail_before_backend_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BackendMustNotStart:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("invalid models must not create an upstream client")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackendMustNotStart)
    values = state_values(god="auto", code="auto", fast="auto")
    with client_for(values) as client:
        missing = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "mn/missing", "messages": []},
        )
        invalid = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": 42, "messages": []},
        )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "model_not_found"
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "invalid_model"


@pytest.mark.parametrize(
    "field",
    ["max_tokens", "max_completion_tokens", "max_output_tokens"],
)
def test_output_limit_is_enforced_before_backend_creation(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    class BackendMustNotStart:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("invalid output limits must not reach a backend")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackendMustNotStart)
    values = state_values(god="auto", code="auto", fast="auto")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={
                "model": "mn/fast",
                "messages": [],
                field: 8193,
            },
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "max_tokens_exceeded"


class FakeUpstreamResponse:
    def __init__(
        self,
        status_code: int,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        chunks: list[bytes] | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}
        self.chunks = chunks
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True

    async def aread(self) -> bytes:
        return self.body

    async def aiter_bytes(self) -> AsyncIterator[bytes]:
        if self.chunks is not None:
            for chunk in self.chunks:
                yield chunk
            return
        yield self.body


class RecordingSuccessClient:
    urls: list[str] = []
    bodies: list[bytes] = []
    headers: list[dict[str, str]] = []
    responses: list[FakeUpstreamResponse] = []
    closed = False

    @classmethod
    def reset(cls) -> None:
        cls.urls = []
        cls.bodies = []
        cls.headers = []
        cls.responses = []
        cls.closed = False

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def build_request(self, _method: str, url: str, **kwargs: object) -> object:
        body = kwargs.get("content", b"")
        headers = kwargs.get("headers", {})
        assert isinstance(body, bytes)
        assert isinstance(headers, dict)
        self.__class__.urls.append(url)
        self.__class__.bodies.append(body)
        self.__class__.headers.append(headers)
        return object()

    async def send(
        self,
        _request: object,
        *,
        stream: bool,
    ) -> FakeUpstreamResponse:
        assert stream is True
        response = FakeUpstreamResponse(
            200,
            b'{"ok":true}',
            {"content-type": "application/json"},
        )
        self.__class__.responses.append(response)
        return response

    async def aclose(self) -> None:
        self.__class__.closed = True


def test_routes_code_to_its_backend_and_rewrites_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RecordingSuccessClient.reset()
    monkeypatch.setattr(gateway.httpx, "AsyncClient", RecordingSuccessClient)
    values = state_values(god="stopped", code="started", fast="stopped")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(
                **{
                    "Content-Type": "application/json",
                    "User-Agent": "gateway-test",
                    "X-Request-ID": "request-code",
                }
            ),
            json={"model": "ornith-code", "messages": []},
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert RecordingSuccessClient.urls == [
        "https://code.backend.example/v1/chat/completions"
    ]
    assert json.loads(RecordingSuccessClient.bodies[0])["model"] == "mn/code"
    upstream_headers = {
        key.lower(): value for key, value in RecordingSuccessClient.headers[0].items()
    }
    assert upstream_headers["modal-key"] == "proxy-key"
    assert upstream_headers["modal-secret"] == "proxy-secret"
    assert upstream_headers["x-request-id"] == "request-code"
    assert "authorization" not in upstream_headers


class ColdStartClient(RecordingSuccessClient):
    send_count = 0
    health_urls: list[str] = []

    @classmethod
    def reset(cls) -> None:
        super().reset()
        cls.send_count = 0
        cls.health_urls = []

    async def send(
        self,
        _request: object,
        *,
        stream: bool,
    ) -> FakeUpstreamResponse:
        assert stream is True
        self.__class__.send_count += 1
        if self.send_count == 1:
            response = FakeUpstreamResponse(503)
        else:
            response = FakeUpstreamResponse(
                200,
                b'{"ok":true}',
                {"content-type": "application/json"},
            )
        self.__class__.responses.append(response)
        return response

    async def get(self, url: str, **_kwargs: object) -> FakeUpstreamResponse:
        self.__class__.health_urls.append(url)
        return FakeUpstreamResponse(200)


def test_code_cold_start_polls_and_retries_only_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ColdStartClient.reset()
    sleeps: list[int] = []

    async def fake_sleep(seconds: int) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(gateway.httpx, "AsyncClient", ColdStartClient)
    monkeypatch.setattr(gateway.asyncio, "sleep", fake_sleep)
    values = state_values(god="stopped", code="auto", fast="auto")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "mn/code", "messages": []},
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert ColdStartClient.send_count == 2
    assert ColdStartClient.health_urls == ["https://code.backend.example/health"]
    assert sleeps == [30]
    assert ColdStartClient.urls == [
        "https://code.backend.example/v1/chat/completions",
        "https://code.backend.example/v1/chat/completions",
    ]
    assert all(
        json.loads(body)["model"] == "mn/code"
        for body in ColdStartClient.bodies
    )


class BackoffColdStartClient(ColdStartClient):
    health_count = 0

    @classmethod
    def reset(cls) -> None:
        super().reset()
        cls.health_count = 0

    async def get(self, url: str, **_kwargs: object) -> FakeUpstreamResponse:
        self.__class__.health_urls.append(url)
        self.__class__.health_count += 1
        return FakeUpstreamResponse(
            200 if self.health_count == 3 else 503,
        )


def test_cold_start_health_checks_use_exponential_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    BackoffColdStartClient.reset()
    sleeps: list[int] = []

    async def fake_sleep(seconds: int) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackoffColdStartClient)
    monkeypatch.setattr(gateway.asyncio, "sleep", fake_sleep)
    values = state_values(god="auto", code="auto", fast="auto")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "mn/fast", "messages": []},
        )

    assert response.status_code == 200
    assert sleeps == [30, 60, 120]
    assert BackoffColdStartClient.health_urls == [
        "https://fast.backend.example/health",
        "https://fast.backend.example/health",
        "https://fast.backend.example/health",
    ]


def test_wake_targets_only_requested_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ColdStartClient.reset()
    monkeypatch.setattr(gateway.httpx, "AsyncClient", ColdStartClient)
    values = state_values(god="stopped", code="stopped", fast="auto")
    with client_for(values) as client:
        response = client.post(
            "/wake",
            headers=auth_headers(),
            params={"model": "mn/fast"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "model": "mn/fast"}
    assert ColdStartClient.health_urls == ["https://fast.backend.example/health"]
    assert ColdStartClient.send_count == 0


class StopDuringStartState(FakeState):
    def __init__(self, values: dict[str, object]) -> None:
        super().__init__(values)
        self.code_lifecycle_reads = 0

    def get(self, key: str, default: object = None) -> object:
        if key == "model:code:lifecycle":
            self.code_lifecycle_reads += 1
            return lifecycle(
                "auto" if self.code_lifecycle_reads == 1 else "stopped"
            )
        return super().get(key, default)


def test_stop_during_code_cold_start_prevents_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ColdStartClient.reset()
    monkeypatch.setattr(gateway.httpx, "AsyncClient", ColdStartClient)
    state = StopDuringStartState(state_values(god="auto", fast="auto"))
    with client_for({}, state=state) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "mn/code", "messages": []},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_stopped"
    assert ColdStartClient.send_count == 1
    assert ColdStartClient.health_urls == []
    assert ColdStartClient.urls == [
        "https://code.backend.example/v1/chat/completions"
    ]


class Bodyful503Client(ColdStartClient):
    async def send(
        self,
        _request: object,
        *,
        stream: bool,
    ) -> FakeUpstreamResponse:
        assert stream is True
        self.__class__.send_count += 1
        return FakeUpstreamResponse(
            503,
            b'{"error":{"message":"overloaded"}}',
            {"content-type": "application/json"},
        )

    async def get(self, *_args: object, **_kwargs: object) -> FakeUpstreamResponse:
        raise AssertionError("application 503 must not trigger health polling")


def test_bodyful_application_503_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    Bodyful503Client.reset()
    monkeypatch.setattr(gateway.httpx, "AsyncClient", Bodyful503Client)
    values = state_values(god="auto", code="auto", fast="auto")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "mn/fast", "messages": []},
        )

    assert response.status_code == 503
    assert response.json()["error"]["message"] == "overloaded"
    assert Bodyful503Client.send_count == 1
    assert Bodyful503Client.urls == [
        "https://fast.backend.example/v1/chat/completions"
    ]


class StreamingClient(RecordingSuccessClient):
    async def send(
        self,
        _request: object,
        *,
        stream: bool,
    ) -> FakeUpstreamResponse:
        assert stream is True
        response = FakeUpstreamResponse(
            200,
            headers={
                "content-type": "text/event-stream",
                "x-private-header": "must-not-pass",
            },
            chunks=[
                b"data: first\n\n",
                b"data: [DONE]\n\n",
            ],
        )
        self.__class__.responses.append(response)
        return response


def test_non_default_streaming_and_cleanup_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    StreamingClient.reset()
    monkeypatch.setattr(gateway.httpx, "AsyncClient", StreamingClient)
    values = state_values(god="stopped", code="stopped", fast="started")
    with client_for(values) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(**{"X-Request-ID": "client-request-id"}),
            json={"model": "mn/fast", "messages": [], "stream": True},
        )

    assert response.status_code == 200
    assert response.content == b"data: first\n\ndata: [DONE]\n\n"
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-request-id"] == "client-request-id"
    assert "x-private-header" not in response.headers
    assert StreamingClient.responses[0].closed is True
    assert StreamingClient.closed is True
