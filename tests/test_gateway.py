from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from mn_uncensored import gateway
from mn_uncensored.gateway import create_app
from mn_uncensored.security import token_key


MODEL = "nuri/ornith-397b-abliterated"
TOKEN = "sk-mn-test-token"


class FakeState:
    def __init__(self, values: dict[str, object] | None = None) -> None:
        self.values = values or {}

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)


def client_for(state_values: dict[str, object]) -> TestClient:
    app = create_app(
        state=FakeState(state_values),
        backend_url="https://backend.example",
        context_window=65536,
        max_output_tokens=8192,
        model=MODEL,
        proxy_key="proxy-key",
        proxy_secret="proxy-secret",
    )
    return TestClient(app)


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


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


def test_models_are_available_without_waking_backend() -> None:
    state = {
        "desired_state": "stopped",
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    with client_for(state) as client:
        response = client.get("/v1/models", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == MODEL
    assert response.json()["data"][0]["context_length"] == 65536


def test_stopped_model_returns_structured_503_without_backend_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BackendMustNotStart:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("stopped mode must not create an upstream client")

    monkeypatch.setattr(gateway.httpx, "AsyncClient", BackendMustNotStart)
    state = {
        "desired_state": "stopped",
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    with client_for(state) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": MODEL, "messages": []},
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_stopped"
    assert response.headers["retry-after"] == "15"


def test_revoked_token_is_rejected() -> None:
    state = {
        token_key(TOKEN): {"active": False, "name": "revoked"},
    }
    with client_for(state) as client:
        response = client.get("/status", headers=auth_headers())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_api_token"


class FakeUpstreamResponse:
    def __init__(
        self,
        status_code: int,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}

    async def aclose(self) -> None:
        return None

    async def aread(self) -> bytes:
        return self.body

    async def aiter_raw(self) -> AsyncIterator[bytes]:
        yield self.body

    async def aiter_bytes(self) -> AsyncIterator[bytes]:
        yield self.body


class FakeAutoStartClient:
    send_count = 0
    get_count = 0
    built_bodies: list[bytes] = []

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def build_request(self, *args: object, **kwargs: object) -> object:
        content = kwargs.get("content", b"")
        assert isinstance(content, bytes)
        self.__class__.built_bodies.append(content)
        return object()

    async def send(
        self,
        _request: object,
        *,
        stream: bool,
    ) -> FakeUpstreamResponse:
        assert stream is True
        self.__class__.send_count += 1
        if self.send_count == 1:
            return FakeUpstreamResponse(503)
        return FakeUpstreamResponse(
            200,
            b'{"ok":true}',
            {"content-type": "application/json"},
        )

    async def get(self, *args: object, **kwargs: object) -> FakeUpstreamResponse:
        self.__class__.get_count += 1
        return FakeUpstreamResponse(200)

    async def aclose(self) -> None:
        return None


def test_auto_mode_waits_through_cold_start_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeAutoStartClient.send_count = 0
    FakeAutoStartClient.get_count = 0
    FakeAutoStartClient.built_bodies = []
    monkeypatch.setattr(gateway.httpx, "AsyncClient", FakeAutoStartClient)
    state = {
        "desired_state": "auto",
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    with client_for(state) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": "client-alias", "messages": []},
        )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert FakeAutoStartClient.send_count == 2
    assert FakeAutoStartClient.get_count == 1
    assert len(FakeAutoStartClient.built_bodies) == 2
    for body in FakeAutoStartClient.built_bodies:
        assert b'"model":"nuri/ornith-397b-abliterated"' in body


def test_wake_endpoint_is_available_in_auto_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gateway.httpx, "AsyncClient", FakeAutoStartClient)
    state = {
        "desired_state": "auto",
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    with client_for(state) as client:
        response = client.post("/wake", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


class StopDuringStartState(FakeState):
    def __init__(self, values: dict[str, object]) -> None:
        super().__init__(values)
        self.desired_state_reads = 0

    def get(self, key: str, default: object = None) -> object:
        if key == "desired_state":
            self.desired_state_reads += 1
            return "auto" if self.desired_state_reads == 1 else "stopped"
        return super().get(key, default)


def test_stop_during_cold_start_prevents_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeAutoStartClient.send_count = 0
    FakeAutoStartClient.get_count = 0
    FakeAutoStartClient.built_bodies = []
    monkeypatch.setattr(gateway.httpx, "AsyncClient", FakeAutoStartClient)
    state = StopDuringStartState(
        {token_key(TOKEN): {"active": True, "name": "owner"}}
    )
    app = create_app(
        state=state,
        backend_url="https://backend.example",
        context_window=65536,
        max_output_tokens=8192,
        model=MODEL,
        proxy_key="proxy-key",
        proxy_secret="proxy-secret",
    )
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": MODEL, "messages": []},
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_stopped"
    assert FakeAutoStartClient.send_count == 1
    assert FakeAutoStartClient.get_count == 0


class Bodyful503Client(FakeAutoStartClient):
    async def send(
        self,
        _request: object,
        *,
        stream: bool,
    ) -> FakeUpstreamResponse:
        self.__class__.send_count += 1
        return FakeUpstreamResponse(
            503,
            b'{"error":{"message":"overloaded"}}',
            {"content-type": "application/json"},
        )

    async def get(self, *args: object, **kwargs: object) -> FakeUpstreamResponse:
        raise AssertionError("application 503 must not trigger health polling")


def test_bodyful_application_503_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    Bodyful503Client.send_count = 0
    Bodyful503Client.built_bodies = []
    monkeypatch.setattr(gateway.httpx, "AsyncClient", Bodyful503Client)
    state = {
        "desired_state": "auto",
        token_key(TOKEN): {"active": True, "name": "owner"},
    }
    with client_for(state) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth_headers(),
            json={"model": MODEL, "messages": []},
        )
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "overloaded"
    assert Bodyful503Client.send_count == 1
