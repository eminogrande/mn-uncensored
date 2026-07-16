from __future__ import annotations

from mn_uncensored.settings import load_settings
from mn_uncensored.vllm import build_vllm_command


def argument_value(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def test_vllm_commands_are_model_specific() -> None:
    settings = load_settings()

    for key, model in settings.models.items():
        command = build_vllm_command(model, model.hf_model)
        assert command[:3] == ["vllm", "serve", model.hf_model]
        assert argument_value(command, "--served-model-name") == model.model
        assert argument_value(command, "--revision") == model.hf_revision
        assert argument_value(command, "--max-model-len") == "131072"
        assert argument_value(command, "--tensor-parallel-size") == str(
            model.gpu_count
        )
        assert argument_value(command, "--tool-call-parser") == model.tool_call_parser
        assert argument_value(command, "--reasoning-parser") == "qwen3"
        assert "--language-model-only" in command
        assert "--enable-prefix-caching" not in command
        assert key in {"god", "code", "fast"}


def test_code_uses_ornith_tool_parser() -> None:
    model = load_settings().models["code"]
    command = build_vllm_command(model, model.hf_model)

    assert argument_value(command, "--tool-call-parser") == "qwen3_xml"
