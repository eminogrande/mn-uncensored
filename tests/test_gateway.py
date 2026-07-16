from __future__ import annotations

from fastapi.testclient import TestClient

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


def test_stopped_model_returns_structured_503() -> None:
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
