from __future__ import annotations

from types import SimpleNamespace

import pytest

from mn_uncensored import cli
from mn_uncensored.settings import ModelSettings, Settings


def model_settings(key: str) -> ModelSettings:
    names = {
        "god": ("God", "mn/god", "mn-god", "GodServer"),
        "code": ("Code", "mn/code", "mn-code", "CodeServer"),
        "fast": ("Fast", "mn/fast", "mn-fast", "FastServer"),
    }
    display_name, public_model, app_name, server_name = names[key]
    return ModelSettings(
        aliases=(f"{key}-alias",),
        app_name=app_name,
        backend_url=f"https://{key}.example",
        context_window=131072,
        display_name=display_name,
        fast_boot=True,
        gpu_count=1,
        gpu_hourly_usd=4.54,
        gpu_memory_utilization=0.90,
        gpu_type="H200",
        hf_model=f"test/{key}",
        hf_revision=f"{key}-revision",
        hf_secret_name="",
        key=key,
        kv_cache_dtype="auto",
        language_model_only=True,
        local_snapshot=False,
        max_num_batched_tokens=8192,
        max_num_seqs=1,
        max_output_tokens=16384,
        model=public_model,
        quantization="",
        reasoning_parser="qwen3",
        server_name=server_name,
        tool_call_parser="qwen3_coder",
        trust_remote_code=True,
    )


def settings() -> Settings:
    return Settings(
        default_model="god",
        gateway_url="https://gateway.example",
        idle_shutdown_seconds=600,
        models={
            key: model_settings(key)
            for key in ("god", "code", "fast")
        },
        state_dict="test-state",
    )


class FakeState:
    def __init__(self, desired_states: dict[str, str] | None = None) -> None:
        self.values: dict[str, object] = {}
        for key, desired_state in (desired_states or {}).items():
            self.values[f"model:{key}:lifecycle"] = {
                "schema": 1,
                "desired_state": desired_state,
                "updated_at": "before-test",
            }

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)

    def put(self, key: str, value: object) -> None:
        self.values[key] = value


def desired_state(state: FakeState, key: str) -> str:
    record = state.values[f"model:{key}:lifecycle"]
    assert isinstance(record, dict)
    return str(record["desired_state"])


def test_hermes_launcher_uses_selected_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = settings().models["code"]
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

    def fake_exec_tool(command: list[str], environment: dict[str, str]) -> None:
        captured.update(command=command, environment=environment)
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(cli, "exec_tool", fake_exec_tool)

    with pytest.raises(RuntimeError, match="exec intercepted"):
        cli.launch_hermes(["--yolo"], settings(), selected, "sk-mn-owner")

    assert captured["command"] == [
        "hermes",
        "--provider",
        "custom:mn-uncensored",
        "--model",
        "mn/code",
        "--tui",
        "--yolo",
    ]
    environment = captured["environment"]
    assert isinstance(environment, dict)
    assert environment["MN_API_TOKEN"] == "sk-mn-owner"
    assert environment["HERMES_STREAM_READ_TIMEOUT"] == "2700"
    assert environment["HERMES_STREAM_STALE_TIMEOUT"] == "2700"
    assert len(config_calls) == 7
    assert [
        call[-1]
        for call in config_calls
        if call[-2] == "providers.mn-uncensored.default_model"
    ] == ["mn/code"]
    assert config_calls[0][-2:] == [
        "providers.mn-uncensored.api",
        "https://gateway.example/v1",
    ]


def test_command_launch_passes_selected_model_to_hermes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected: list[str] = []
    monkeypatch.setattr(cli, "require_launch_allowed", lambda *_args: "started")
    monkeypatch.setattr(cli, "owner_token", lambda: "sk-owner")
    monkeypatch.setattr(
        cli,
        "launch_hermes",
        lambda _args, _settings, model, _token: selected.append(model.key),
    )

    cli.command_launch(
        SimpleNamespace(model="code", tool="hermes", tool_args=[]),
        settings(),
    )

    assert selected == ["code"]


def test_stop_only_resets_selected_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"god": "auto", "code": "started", "fast": "stopped"})
    reset_models: list[str] = []
    checked_models: list[str] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)

    def fake_is_stopped(model: ModelSettings) -> bool:
        checked_models.append(model.key)
        return False

    monkeypatch.setattr(cli, "backend_app_is_stopped", fake_is_stopped)
    monkeypatch.setattr(
        cli,
        "reset_backend_to_static",
        lambda model: reset_models.append(model.key),
    )

    cli.command_stop(SimpleNamespace(model="code"), settings())

    assert checked_models == ["code"]
    assert reset_models == ["code"]
    assert desired_state(state, "god") == "auto"
    assert desired_state(state, "code") == "stopped"
    assert desired_state(state, "fast") == "stopped"


def test_auto_redeploys_selected_scale_to_zero_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"god": "stopped", "code": "stopped", "fast": "stopped"})
    deployments: list[tuple[str, str]] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda model, tag: deployments.append((model.key, tag)),
    )

    cli.command_auto(SimpleNamespace(model="code"), settings())

    assert deployments == [("code", "auto-lifecycle")]
    assert desired_state(state, "god") == "stopped"
    assert desired_state(state, "code") == "auto"
    assert desired_state(state, "fast") == "stopped"


def test_auto_deploy_failure_stays_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"code": "stopped"})
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda _model, _tag: (_ for _ in ()).throw(SystemExit(1)),
    )

    with pytest.raises(SystemExit):
        cli.command_auto(SimpleNamespace(model="code"), settings())

    assert desired_state(state, "code") == "stopped"


def test_start_uses_selected_model_app_after_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"god": "auto", "code": "stopped", "fast": "stopped"})
    events: list[str] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda model, tag: events.append(f"deploy:{model.key}:{tag}"),
    )

    def fail_after_lookup(app_name: str, server_name: str) -> object:
        events.append(f"server:{app_name}:{server_name}")
        raise RuntimeError("lookup intercepted")

    monkeypatch.setattr(cli.modal.Server, "from_name", fail_after_lookup)

    with pytest.raises(RuntimeError, match="lookup intercepted"):
        cli.command_start(SimpleNamespace(model="code", timeout=1), settings())

    assert events == [
        "deploy:code:manual-start",
        "server:mn-code:CodeServer",
    ]
    assert desired_state(state, "god") == "auto"
    assert desired_state(state, "code") == "starting"
    assert desired_state(state, "fast") == "stopped"


def test_wake_uses_selected_model_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> SimpleNamespace:
        captured.update(url=url, **kwargs)
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(cli.httpx, "post", fake_post)

    cli.wake_model(settings(), settings().models["fast"], "sk-owner")

    assert captured["url"] == "https://gateway.example/wake"
    assert captured["params"] == {"model": "mn/fast"}
    assert captured["headers"] == {"Authorization": "Bearer sk-owner"}
    assert captured["timeout"] == 45 * 60
    assert captured["follow_redirects"] is True


def test_launch_parser_accepts_model_before_tool() -> None:
    args = cli.build_parser().parse_args(
        ["launch", "--model", "code", "hermes", "--yolo"]
    )

    assert args.command == "launch"
    assert args.model == "code"
    assert args.tool == "hermes"
    assert args.tool_args == ["--yolo"]


def test_parallel_stop_wins_over_running_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"code": "stopped"})
    selected = settings().models["code"]
    health_calls = 0

    class FakeServer:
        def update_autoscaler(self, **_kwargs: object) -> None:
            return None

    class FakeResponse:
        status_code = 200

    class FakeClient:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, *_args: object, **_kwargs: object) -> FakeResponse:
            nonlocal health_calls
            health_calls += 1
            state.put(
                selected.lifecycle_key,
                {
                    "schema": 1,
                    "desired_state": "stopped",
                    "updated_at": "parallel-stop",
                },
            )
            return FakeResponse()

    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: False)
    monkeypatch.setattr(
        cli.modal.Server,
        "from_name",
        lambda *_args: FakeServer(),
    )
    monkeypatch.setattr(cli, "backend_headers", lambda: {})
    monkeypatch.setattr(cli.httpx, "Client", FakeClient)

    cli.start_model(
        SimpleNamespace(timeout=1),
        settings(),
        selected,
    )

    assert health_calls == 1
    assert desired_state(state, "code") == "stopped"
