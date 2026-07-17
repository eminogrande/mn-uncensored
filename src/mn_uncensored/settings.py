from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "mn.json"


@dataclass(frozen=True)
class ModelSettings:
    aliases: tuple[str, ...]
    app_name: str
    backend_url: str
    context_window: int
    deployment_enabled: bool
    display_name: str
    fast_boot: bool
    gpu_count: int
    gpu_hourly_usd: float
    gpu_memory_utilization: float
    gpu_type: str
    hf_model: str
    hf_revision: str
    hf_secret_name: str
    key: str
    kv_cache_dtype: str
    language_model_only: bool
    local_snapshot: bool
    max_num_batched_tokens: int
    max_num_seqs: int
    max_output_tokens: int
    model: str
    prefix_caching: bool
    quantization: str
    reasoning_parser: str
    requires_cost_acknowledgement: bool
    server_name: str
    tool_call_parser: str
    trust_remote_code: bool

    @property
    def lifecycle_key(self) -> str:
        return f"model:{self.key}:lifecycle"

    @property
    def gpu_label(self) -> str:
        return f"{self.gpu_count} x {self.gpu_type}"


@dataclass(frozen=True)
class Settings:
    default_model: str
    gateway_url: str
    idle_shutdown_seconds: int
    models: dict[str, ModelSettings]
    state_dict: str

    @property
    def api_base_url(self) -> str:
        if not self.gateway_url:
            return ""
        return f"{self.gateway_url.rstrip('/')}/v1"

    @property
    def default(self) -> ModelSettings:
        return self.models[self.default_model]

    @property
    def deployed_models(self) -> dict[str, ModelSettings]:
        return {
            key: model
            for key, model in self.models.items()
            if model.deployment_enabled
        }

    def resolve_model(self, value: str | None) -> ModelSettings:
        candidate = (value or self.default_model).strip()
        if candidate in self.models:
            return self.models[candidate]
        for model in self.models.values():
            if candidate == model.model or candidate in model.aliases:
                return model
        available = ", ".join(self.models)
        raise ValueError(f"Unknown model `{candidate}`. Choose one of: {available}.")


def _required(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ValueError(f"Missing `{key}` in {context}.")
    return data[key]


def _model_settings(key: str, data: dict[str, Any]) -> ModelSettings:
    context = f"model `{key}`"
    model = ModelSettings(
        aliases=tuple(data.get("aliases", [])),
        app_name=str(_required(data, "app_name", context)),
        backend_url=str(_required(data, "backend_url", context)).rstrip("/"),
        context_window=int(_required(data, "context_window", context)),
        deployment_enabled=bool(data.get("deployment_enabled", True)),
        display_name=str(_required(data, "display_name", context)),
        fast_boot=bool(data.get("fast_boot", True)),
        gpu_count=int(_required(data, "gpu_count", context)),
        gpu_hourly_usd=float(_required(data, "gpu_hourly_usd", context)),
        gpu_memory_utilization=float(data.get("gpu_memory_utilization", 0.90)),
        gpu_type=str(_required(data, "gpu_type", context)).upper(),
        hf_model=str(_required(data, "hf_model", context)),
        hf_revision=str(_required(data, "hf_revision", context)),
        hf_secret_name=str(data.get("hf_secret_name", "")),
        key=key,
        kv_cache_dtype=str(data.get("kv_cache_dtype", "fp8")),
        language_model_only=bool(data.get("language_model_only", True)),
        local_snapshot=bool(data.get("local_snapshot", False)),
        max_num_batched_tokens=int(data.get("max_num_batched_tokens", 8192)),
        max_num_seqs=int(data.get("max_num_seqs", 1)),
        max_output_tokens=int(_required(data, "max_output_tokens", context)),
        model=str(_required(data, "model", context)),
        prefix_caching=bool(data.get("prefix_caching", False)),
        quantization=str(data.get("quantization", "")),
        reasoning_parser=str(data.get("reasoning_parser", "")),
        requires_cost_acknowledgement=bool(
            data.get("requires_cost_acknowledgement", False)
        ),
        server_name=str(data.get("server_name", "VllmServer")),
        tool_call_parser=str(data.get("tool_call_parser", "")),
        trust_remote_code=bool(data.get("trust_remote_code", True)),
    )
    if model.model != model.hf_model:
        raise ValueError(
            f"{context} public model ID must equal its exact Hugging Face model ID."
        )
    if model.gpu_count < 1 or model.gpu_count > 8:
        raise ValueError(f"{context} gpu_count must be between 1 and 8.")
    if not 0.5 <= model.gpu_memory_utilization <= 0.95:
        raise ValueError(
            f"{context} gpu_memory_utilization must be between 0.5 and 0.95."
        )
    for name, value in (
        ("context_window", model.context_window),
        ("max_output_tokens", model.max_output_tokens),
        ("max_num_batched_tokens", model.max_num_batched_tokens),
        ("max_num_seqs", model.max_num_seqs),
    ):
        if value < 1:
            raise ValueError(f"{context} {name} must be positive.")
    return model


def load_settings(path: Path | None = None) -> Settings:
    if path is None:
        path = Path(os.getenv("MN_CONFIG_PATH", str(CONFIG_PATH)))
    data = json.loads(path.read_text())
    raw_models = _required(data, "models", "catalog")
    if not isinstance(raw_models, dict) or not raw_models:
        raise ValueError("`models` must be a non-empty object.")
    models = {
        key: _model_settings(key, model_data)
        for key, model_data in raw_models.items()
    }
    default_model = str(_required(data, "default_model", "catalog"))
    if default_model not in models:
        raise ValueError("`default_model` must name a configured model.")
    if not models[default_model].deployment_enabled:
        raise ValueError("`default_model` must be deployment-enabled.")

    identifiers: dict[str, str] = {}
    for key, model in models.items():
        for identifier in (model.model, *model.aliases):
            owner = identifiers.get(identifier)
            if owner is not None:
                raise ValueError(
                    f"Model identifier `{identifier}` is duplicated by `{owner}` and `{key}`."
                )
            identifiers[identifier] = key

    gateway_url = os.getenv(
        "MN_GATEWAY_URL",
        str(_required(data, "gateway_url", "catalog")),
    ).rstrip("/")
    idle_shutdown_seconds = int(
        _required(data, "idle_shutdown_seconds", "catalog")
    )
    if not 1 <= idle_shutdown_seconds <= 300:
        raise ValueError(
            "`idle_shutdown_seconds` must be between 1 and 300 seconds."
        )

    return Settings(
        default_model=default_model,
        gateway_url=gateway_url,
        idle_shutdown_seconds=idle_shutdown_seconds,
        models=models,
        state_dict=str(_required(data, "state_dict", "catalog")),
    )
