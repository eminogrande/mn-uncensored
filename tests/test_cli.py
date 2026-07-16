from __future__ import annotations

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


class FakeState:
    def __init__(self, desired_state: str) -> None:
        self.values: dict[str, object] = {"desired_state": desired_state}

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)

    def put(self, key: str, value: object) -> None:
        self.values[key] = value


def test_stop_uses_immutable_rollover(monkeypatch: pytest.MonkeyPatch) -> None:
    state = FakeState("auto")
    commands: list[list[str]] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "modal_cli_path", lambda: "/usr/local/bin/modal")
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _settings: False)
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda command, **_kwargs: (
            commands.append(command) or SimpleNamespace(returncode=0)
        ),
    )

    cli.command_stop(SimpleNamespace(), settings())

    assert commands == [
        [
            "/usr/local/bin/modal",
            "app",
            "rollover",
            "test-app",
            "--strategy",
            "recreate",
        ]
    ]
    assert state.values["desired_state"] == "stopped"


def test_auto_redeploys_scale_to_zero_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState("stopped")
    tags: list[str] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _settings: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda _settings, tag: tags.append(tag),
    )

    cli.command_auto(SimpleNamespace(), settings())

    assert tags == ["auto-lifecycle"]
    assert state.values["desired_state"] == "auto"


def test_auto_deploy_failure_stays_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState("stopped")
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _settings: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda _settings, _tag: (_ for _ in ()).throw(SystemExit(1)),
    )

    with pytest.raises(SystemExit):
        cli.command_auto(SimpleNamespace(), settings())

    assert state.values["desired_state"] == "stopped"


def test_start_redeploys_before_server_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState("stopped")
    events: list[str] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _settings: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda _settings, _tag: events.append("deploy"),
    )

    def fail_after_deploy(*_args: object, **_kwargs: object) -> object:
        events.append("server")
        raise RuntimeError("lookup intercepted")

    monkeypatch.setattr(cli.modal.Server, "from_name", fail_after_deploy)

    with pytest.raises(RuntimeError, match="lookup intercepted"):
        cli.command_start(SimpleNamespace(timeout=1), settings())

    assert events == ["deploy", "server"]
    assert state.values["desired_state"] == "starting"
