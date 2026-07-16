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
        "ornith397": (
            "Ornith 397B",
            "mn/ornith-397b",
            "mn-ornith-397b",
            "Ornith397Server",
        ),
    }
    display_name, public_model, app_name, server_name = names[key]
    is_large = key == "ornith397"
    return ModelSettings(
        aliases=(
            ("nuri/ornith-397b-abliterated",)
            if is_large
            else (f"{key}-alias",)
        ),
        app_name=app_name,
        backend_url=f"https://{key}.example",
        context_window=32768 if is_large else 131072,
        deployment_enabled=True,
        display_name=display_name,
        fast_boot=True,
        gpu_count=2 if is_large else 1,
        gpu_hourly_usd=9.0792 if is_large else 4.54,
        gpu_memory_utilization=0.90,
        gpu_type="H200",
        hf_model=f"test/{key}",
        hf_revision=f"{key}-revision",
        hf_secret_name="",
        key=key,
        kv_cache_dtype="fp8" if is_large else "auto",
        language_model_only=not is_large,
        local_snapshot=False,
        max_num_batched_tokens=8192,
        max_num_seqs=1,
        max_output_tokens=8192 if is_large else 16384,
        model=public_model,
        prefix_caching=False,
        quantization="",
        reasoning_parser="qwen3",
        requires_cost_acknowledgement=is_large,
        server_name=server_name,
        tool_call_parser="qwen3_xml",
        trust_remote_code=True,
    )


def settings() -> Settings:
    return Settings(
        default_model="god",
        gateway_url="https://gateway.example",
        idle_shutdown_seconds=300,
        models={
            key: model_settings(key)
            for key in ("god", "code", "fast", "ornith397")
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


def test_expensive_model_cannot_be_started_without_acknowledgement() -> None:
    with pytest.raises(SystemExit):
        cli.command_start(
            SimpleNamespace(model="ornith397"),
            settings(),
        )


def test_expensive_model_cannot_be_armed_or_mutate_state_without_acknowledgement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "state_dict",
        lambda _settings: pytest.fail("disabled model must fail before state access"),
    )

    with pytest.raises(SystemExit):
        cli.command_auto(
            SimpleNamespace(model="ornith397"),
            settings(),
        )


def test_stop_only_resets_selected_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState(
        {
            "god": "auto",
            "code": "started",
            "fast": "stopped",
            "ornith397": "auto",
        }
    )
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
    assert desired_state(state, "ornith397") == "auto"


def test_static_reset_retries_transient_modal_rollover(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    return_codes = iter([1, 0])
    sleeps: list[int] = []
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=next(return_codes)),
    )
    monkeypatch.setattr(cli.time, "sleep", sleeps.append)

    cli.reset_backend_to_static(settings().models["code"])

    assert sleeps == [3]


def test_static_reset_fails_after_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1),
    )
    monkeypatch.setattr(cli.time, "sleep", lambda _seconds: None)

    with pytest.raises(SystemExit):
        cli.reset_backend_to_static(settings().models["code"])


def test_auto_redeploys_selected_scale_to_zero_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState(
        {
            "god": "stopped",
            "code": "stopped",
            "fast": "stopped",
            "ornith397": "stopped",
        }
    )
    deployments: list[tuple[str, str]] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: True)
    monkeypatch.setattr(
        cli,
        "deploy_backend",
        lambda model, tag: deployments.append((model.key, tag)),
    )
    monkeypatch.setattr(cli, "enforce_scale_to_zero", lambda *_args: None)

    cli.command_auto(SimpleNamespace(model="code"), settings())

    assert deployments == [("code", "auto-lifecycle")]
    assert desired_state(state, "god") == "stopped"
    assert desired_state(state, "code") == "auto"
    assert desired_state(state, "fast") == "stopped"
    assert desired_state(state, "ornith397") == "stopped"


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


def test_auto_reapplies_scale_to_zero_to_deployed_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"code": "auto"})
    enforced: list[str] = []
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: False)
    monkeypatch.setattr(
        cli,
        "enforce_scale_to_zero",
        lambda model, _settings: enforced.append(model.key),
    )

    cli.command_auto(SimpleNamespace(model="code"), settings())

    assert enforced == ["code"]
    assert desired_state(state, "code") == "auto"


def test_scale_to_zero_policy_never_keeps_a_warm_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeServer:
        def update_autoscaler(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(
        cli.modal.Server,
        "from_name",
        lambda *_args: FakeServer(),
    )

    cli.enforce_scale_to_zero(settings().models["god"], settings())

    assert captured == {
        "min_containers": 0,
        "max_containers": 1,
        "scaledown_window": 300,
    }


def test_auto_policy_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = FakeState({"code": "auto"})
    monkeypatch.setattr(cli, "state_dict", lambda _settings: state)
    monkeypatch.setattr(cli, "backend_app_is_stopped", lambda _model: False)
    monkeypatch.setattr(
        cli,
        "enforce_scale_to_zero",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("Modal failure")),
    )

    with pytest.raises(RuntimeError, match="Modal failure"):
        cli.command_auto(SimpleNamespace(model="code"), settings())

    assert desired_state(state, "code") == "stopped"


def test_start_arms_auto_and_wakes_selected_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, str]] = []
    monkeypatch.setattr(
        cli,
        "command_auto",
        lambda args, _settings: events.append(("auto", args.model)),
    )
    monkeypatch.setattr(cli, "owner_token", lambda: "sk-owner")
    monkeypatch.setattr(
        cli,
        "wake_model",
        lambda _settings, model, token: events.append(
            (f"wake:{model.key}", token)
        ),
    )

    cli.command_start(SimpleNamespace(model="code"), settings())

    assert events == [("auto", "code"), ("wake:code", "sk-owner")]


def test_expensive_start_passes_acknowledgement_to_auto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        cli,
        "command_auto",
        lambda args, _settings: captured.update(
            model=args.model,
            allow_expensive=args.allow_expensive,
        ),
    )
    monkeypatch.setattr(cli, "owner_token", lambda: "sk-owner")
    monkeypatch.setattr(cli, "wake_model", lambda *_args: None)
    monkeypatch.setattr(cli, "print_api_details", lambda *_args: None)

    cli.command_start(
        SimpleNamespace(model="ornith397", allow_expensive=True),
        settings(),
    )

    assert captured == {
        "model": "ornith397",
        "allow_expensive": True,
    }


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


def test_start_parser_requires_explicit_model() -> None:
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["start"])

    args = parser.parse_args(["start", "fast"])
    assert args.model == "fast"

    expensive = parser.parse_args(
        ["start", "ornith397", "--allow-expensive"]
    )
    assert expensive.model == "ornith397"
    assert expensive.allow_expensive is True


def test_auto_parser_requires_explicit_model() -> None:
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["auto"])

    args = parser.parse_args(["auto", "code"])
    assert args.model == "code"
