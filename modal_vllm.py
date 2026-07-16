from __future__ import annotations

import os
import subprocess

import modal

from mn_uncensored.settings import load_settings
from mn_uncensored.vllm import build_vllm_command


settings = load_settings()
model_key = os.getenv("MN_MODEL", settings.default_model)
model = settings.resolve_model(model_key)

MAX_CONTAINERS = 1
ROUTING_REGION = "eu-west"
VLLM_PORT = 8000
STARTUP_TIMEOUT_SECONDS = 90 * 60
LOCAL_MODEL_PATH = (
    "/root/.cache/huggingface/models--"
    f"{model.hf_model.replace('/', '--')}/snapshots/{model.hf_revision}"
)
MODEL_SOURCE = LOCAL_MODEL_PATH if model.local_snapshot else model.hf_model

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
            "HF_HUB_OFFLINE": "1" if model.local_snapshot else "0",
            "HF_XET_HIGH_PERFORMANCE": "1",
            "MN_CONFIG_PATH": "/root/mn/config/mn.json",
            "VLLM_LOG_STATS_INTERVAL": "10",
        }
    )
    .add_local_file("config/mn.json", "/root/mn/config/mn.json", copy=True)
    .add_local_python_source("mn_uncensored")
)

hf_cache = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-compile-cache", create_if_missing=True)
secrets = (
    [modal.Secret.from_name(model.hf_secret_name)]
    if model.hf_secret_name
    else []
)

app = modal.App(model.app_name)


def vllm_command() -> list[str]:
    return build_vllm_command(model, MODEL_SOURCE, port=VLLM_PORT)


@app.server(
    image=vllm_image,
    gpu=f"{model.gpu_type}:{model.gpu_count}",
    min_containers=0,
    max_containers=MAX_CONTAINERS,
    scaledown_window=settings.idle_shutdown_seconds,
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
        if model.local_snapshot and not os.path.isdir(LOCAL_MODEL_PATH):
            raise RuntimeError(
                f"Pinned local model snapshot is missing: {LOCAL_MODEL_PATH}"
            )
        command = vllm_command()
        print(
            "Starting private vLLM server",
            f"catalog_key={model.key}",
            f"model={model.hf_model}",
            f"revision={model.hf_revision}",
            f"served_model={model.model}",
            f"source={'local-snapshot' if model.local_snapshot else 'huggingface'}",
            f"gpu={model.gpu_type}:{model.gpu_count}",
            f"max_model_len={model.context_window}",
        )
        self.process = subprocess.Popen(command)

    @modal.exit()
    def stop(self) -> None:
        self.process.terminate()
