from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from mn_uncensored import cli
from mn_uncensored.settings import Settings


def settings() -> Settings:
    return Settings(
        app_name="test-app",
        backend_url="https://backend.example",
        context_window=65536,
        gateway_url="https://gateway.example",
        gpu_hourly_usd=9.08,
        idle_shutdown_seconds=600,
        max_output_tokens=8192,
        model="nuri/ornith-397b-abliterated",
        server_name="VllmServer",
        state_dict="test-state",
    )


def test_hermes_launcher_uses_custom_openai_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    config_calls: list[list[str]] = []

    monkeypatch.setattr(cli.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda command, **_kwargs: (
            config_calls.append(command) or SimpleNamespace(returncode=0)
        ),
    )

    def fake_execvpe(
        executable: str,
        command: list[str],
        environment: dict[str, str],
    ) -> None:
        captured.update(
            executable=executable,
            command=command,
            environment=environment,
        )
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(cli.os, "execvpe", fake_execvpe)

    with pytest.raises(RuntimeError, match="exec intercepted"):
        cli.launch_hermes(["--yolo"], settings(), "sk-mn-owner")

    assert captured["executable"] == "/usr/local/bin/hermes"
    assert captured["command"] == [
        "/usr/local/bin/hermes",
        "--provider",
        "custom:mn-uncensored",
        "--model",
        "nuri/ornith-397b-abliterated",
        "--tui",
        "--yolo",
    ]
    environment = captured["environment"]
    assert isinstance(environment, dict)
    assert environment["MN_API_TOKEN"] == "sk-mn-owner"
    assert environment["HERMES_STREAM_READ_TIMEOUT"] == "2700"
    assert environment["HERMES_STREAM_STALE_TIMEOUT"] == "2700"
    assert len(config_calls) == 7
    assert config_calls[0][-2:] == [
        "providers.mn-uncensored.api",
        "https://gateway.example/v1",
    ]


def test_backend_container_ids_only_returns_model_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "modal_cli_path", lambda: "/usr/local/bin/modal")
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "container_id": "model-container",
                        "app_name": "test-app",
                    },
                    {
                        "container_id": "gateway-container",
                        "app_name": "mn-uncensored-api",
                    },
                ]
            ),
        ),
    )
    assert cli.backend_container_ids(settings()) == ["model-container"]
