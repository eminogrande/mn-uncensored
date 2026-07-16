from __future__ import annotations

from mn_uncensored.settings import load_settings
from mn_uncensored.vllm import build_runtime_environment, build_vllm_command


def argument_value(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def test_vllm_commands_are_model_specific() -> None:
    settings = load_settings()

    for key, model in settings.models.items():
        command = build_vllm_command(model, model.hf_model)
        assert command[:3] == ["vllm", "serve", model.hf_model]
        assert argument_value(command, "--served-model-name") == model.model
        assert argument_value(command, "--revision") == model.hf_revision
        assert argument_value(command, "--max-model-len") == (
            "32768" if key == "ornith397" else "131072"
        )
        assert argument_value(command, "--tensor-parallel-size") == str(
            model.gpu_count
        )
        assert argument_value(command, "--tool-call-parser") == model.tool_call_parser
        if key == "ornith397":
            assert "--language-model-only" not in command
        else:
            assert "--language-model-only" in command
        assert model.tool_call_parser == "qwen3_xml"
        assert argument_value(command, "--reasoning-parser") == "qwen3"
        assert (
            argument_value(command, "--default-chat-template-kwargs")
            == '{"enable_thinking": false}'
        )
        assert "--enable-prefix-caching" not in command
        assert key in {"god", "code", "fast", "ornith397"}


def test_catalog_uses_model_chat_template_tool_parser() -> None:
    settings = load_settings()

    assert {
        argument_value(
            build_vllm_command(model, model.hf_model),
            "--tool-call-parser",
        )
        for model in settings.models.values()
    } == {"qwen3_xml"}


def test_runtime_environment_preserves_selected_profile() -> None:
    settings = load_settings()

    for key, model in settings.models.items():
        environment = build_runtime_environment(model)
        assert environment["MN_MODEL"] == key
        assert environment["HF_HUB_OFFLINE"] == "0"
