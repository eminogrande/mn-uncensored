from __future__ import annotations

import pytest

from mn_uncensored import cli
from mn_uncensored.settings import Settings


def settings() -> Settings:
    return Settings(
        app_name="test-app",
        backend_url="https://backend.example",
        gateway_url="https://gateway.example",
        gpu_hourly_usd=9.08,
        model="nuri/ornith-397b-abliterated",
        server_name="VllmServer",
        state_dict="test-state",
    )


def test_hermes_launcher_uses_custom_openai_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(cli.shutil, "which", lambda name: f"/usr/local/bin/{name}")

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
        "custom",
        "--model",
        "nuri/ornith-397b-abliterated",
        "--tui",
        "--yolo",
    ]
    environment = captured["environment"]
    assert isinstance(environment, dict)
    assert environment["OPENAI_API_KEY"] == "sk-mn-owner"
    assert environment["OPENAI_BASE_URL"] == "https://gateway.example/v1"
