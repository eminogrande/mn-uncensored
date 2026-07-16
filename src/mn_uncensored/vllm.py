from __future__ import annotations

from .settings import ModelSettings


def build_vllm_command(
    model: ModelSettings,
    model_source: str,
    *,
    port: int = 8000,
) -> list[str]:
    command = [
        "vllm",
        "serve",
        model_source,
        "--served-model-name",
        model.model,
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--tensor-parallel-size",
        str(model.gpu_count),
        "--max-model-len",
        str(model.context_window),
        "--gpu-memory-utilization",
        str(model.gpu_memory_utilization),
        "--kv-cache-dtype",
        model.kv_cache_dtype,
        "--mamba-cache-dtype",
        "float32",
        "--safetensors-load-strategy",
        "prefetch",
        "--max-num-seqs",
        str(model.max_num_seqs),
        "--max-num-batched-tokens",
        str(model.max_num_batched_tokens),
        "--enable-chunked-prefill",
        "--no-enable-log-requests",
        "--disable-uvicorn-access-log",
    ]

    if model.language_model_only:
        command.append("--language-model-only")
    if not model.local_snapshot:
        command.extend(["--revision", model.hf_revision])
    if model.fast_boot:
        command.append("--enforce-eager")
    if model.trust_remote_code:
        command.append("--trust-remote-code")
    if model.quantization:
        command.extend(["--quantization", model.quantization])
    if model.reasoning_parser:
        command.extend(["--reasoning-parser", model.reasoning_parser])
    if model.tool_call_parser:
        command.extend(
            [
                "--enable-auto-tool-choice",
                "--tool-call-parser",
                model.tool_call_parser,
            ]
        )
    return command
