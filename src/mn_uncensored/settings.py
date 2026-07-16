from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "mn.json"


@dataclass(frozen=True)
class Settings:
    app_name: str
    backend_url: str
    context_window: int
    gateway_url: str
    gpu_hourly_usd: float
    idle_shutdown_seconds: int
    max_output_tokens: int
    model: str
    server_name: str
    state_dict: str

    @property
    def api_base_url(self) -> str:
        if not self.gateway_url:
            return ""
        return f"{self.gateway_url.rstrip('/')}/v1"


def load_settings() -> Settings:
    data = json.loads(CONFIG_PATH.read_text())
    gateway_url = os.getenv("MN_GATEWAY_URL", data["gateway_url"]).rstrip("/")
    return Settings(
        app_name=data["app_name"],
        backend_url=data["backend_url"].rstrip("/"),
        context_window=int(data["context_window"]),
        gateway_url=gateway_url,
        gpu_hourly_usd=float(data["gpu_hourly_usd"]),
        idle_shutdown_seconds=int(data["idle_shutdown_seconds"]),
        max_output_tokens=int(data["max_output_tokens"]),
        model=data["model"],
        server_name=data["server_name"],
        state_dict=data["state_dict"],
    )
