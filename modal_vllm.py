from __future__ import annotations

import os
import subprocess

import modal


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "cebeuq/Ornith-1.0-397B-abliterated-W4A16",
)
MODEL_REVISION = os.getenv(
    "MODEL_REVISION",
    "e5651d291be1c65ff1360eee47ab533ab13b3d97",
)
SERVED_MODEL_NAME = os.getenv(
    "SERVED_MODEL_NAME",
    "nuri/ornith-397b-abliterated",
)

GPU_TYPE = os.getenv("GPU_TYPE", "H200").upper()
GPU_COUNT = int(os.getenv("GPU_COUNT", "2"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "65536"))
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.90"))

FAST_BOOT = env_bool("FAST_BOOT", True)
LOCAL_SNAPSHOT = env_bool("LOCAL_SNAPSHOT", True)
TRUST_REMOTE_CODE = env_bool("TRUST_REMOTE_CODE", True)
QUANTIZATION = os.getenv("QUANTIZATION", "").strip()
HF_SECRET_NAME = os.getenv("HF_SECRET_NAME", "").strip()

MAX_CONTAINERS = int(os.getenv("MAX_CONTAINERS", "1"))
SCALEDOWN_WINDOW_SECONDS = int(os.getenv("SCALEDOWN_WINDOW_SECONDS", "600"))
ROUTING_REGION = os.getenv("ROUTING_REGION", "eu-west")

VLLM_PORT = 8000
STARTUP_TIMEOUT_SECONDS = 90 * 60
LOCAL_MODEL_PATH = (
    "/root/.cache/huggingface/models--"
    f"{MODEL_NAME.replace('/', '--')}/snapshots/{MODEL_REVISION}"
)
MODEL_SOURCE = LOCAL_MODEL_PATH if LOCAL_SNAPSHOT else MODEL_NAME

if GPU_COUNT < 1 or GPU_COUNT > 8:
    raise ValueError("GPU_COUNT must be between 1 and 8")
if MAX_CONTAINERS != 1:
    raise ValueError("Keep MAX_CONTAINERS=1 until the deployment has been cost-tested")
if not 0.5 <= GPU_MEMORY_UTILIZATION <= 0.95:
    raise ValueError("GPU_MEMORY_UTILIZATION must be between 0.5 and 0.95")


vllm_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.9.0-devel-ubuntu22.04",
        add_python="3.12",
    )
    .entrypoint([])
    .uv_pip_install("vllm==0.21.0")
    .env(
        {
            "HF_HUB_CACHE": "/root/.cache/huggingface",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HUB_OFFLINE": "1" if LOCAL_SNAPSHOT else "0",
            "HF_XET_HIGH_PERFORMANCE": "1",
            "VLLM_LOG_STATS_INTERVAL": "10",
        }
    )
)

hf_cache = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-compile-cache", create_if_missing=True)
secrets = [modal.Secret.from_name(HF_SECRET_NAME)] if HF_SECRET_NAME else []

app = modal.App("nuri-ornith-397b")


@app.server(
    image=vllm_image,
    gpu=f"{GPU_TYPE}:{GPU_COUNT}",
    min_containers=0,
    max_containers=MAX_CONTAINERS,
    scaledown_window=SCALEDOWN_WINDOW_SECONDS,
    startup_timeout=STARTUP_TIMEOUT_SECONDS,
    port=VLLM_PORT,
    routing_region=ROUTING_REGION,
    unauthenticated=False,
    secrets=secrets,
    volumes={
        "/root/.cache/huggingface": hf_cache,
        "/root/.cache/vllm": vllm_cache,
    },
)
class VllmServer:
    @modal.enter()
    def start(self) -> None:
        if LOCAL_SNAPSHOT and not os.path.isdir(LOCAL_MODEL_PATH):
            raise RuntimeError(
                f"Pinned local model snapshot is missing: {LOCAL_MODEL_PATH}"
            )
        command = [
            "vllm",
            "serve",
            MODEL_SOURCE,
            "--served-model-name",
            SERVED_MODEL_NAME,
            "--host",
            "0.0.0.0",
            "--port",
            str(VLLM_PORT),
            "--tensor-parallel-size",
            str(GPU_COUNT),
            "--max-model-len",
            str(MAX_MODEL_LEN),
            "--gpu-memory-utilization",
            str(GPU_MEMORY_UTILIZATION),
            "--kv-cache-dtype",
            "fp8",
            "--mamba-cache-dtype",
            "float32",
            "--safetensors-load-strategy",
            "prefetch",
            "--max-num-seqs",
            "1",
            "--max-num-batched-tokens",
            "8192",
            "--enable-chunked-prefill",
            "--enable-prefix-caching",
            "--enable-auto-tool-choice",
            "--tool-call-parser",
            "qwen3_coder",
            "--no-enable-log-requests",
            "--disable-uvicorn-access-log",
        ]

        if not LOCAL_SNAPSHOT:
            command.extend(["--revision", MODEL_REVISION])
        if FAST_BOOT:
            command.append("--enforce-eager")
        if TRUST_REMOTE_CODE:
            command.append("--trust-remote-code")
        if QUANTIZATION:
            command.extend(["--quantization", QUANTIZATION])

        print(
            "Starting private vLLM server",
            f"model={MODEL_NAME}",
            f"revision={MODEL_REVISION}",
            f"source={'local-snapshot' if LOCAL_SNAPSHOT else 'huggingface'}",
            f"gpu={GPU_TYPE}:{GPU_COUNT}",
            f"max_model_len={MAX_MODEL_LEN}",
        )
        self.process = subprocess.Popen(command)

    @modal.exit()
    def stop(self) -> None:
        self.process.terminate()
