from __future__ import annotations

import os

import modal

from mn_uncensored.settings import load_settings


APP_NAME = "mn-uncensored-api"
settings = load_settings()
catalog = {
    key: {
        "aliases": list(model.aliases),
        "backend_url": model.backend_url,
        "context_window": model.context_window,
        "lifecycle_key": model.lifecycle_key,
        "max_output_tokens": model.max_output_tokens,
        "model": model.model,
    }
    for key, model in settings.models.items()
}

image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("fastapi>=0.128,<0.129", "httpx>=0.28,<1")
    .env({"MN_CONFIG_PATH": "/root/mn/config/mn.json"})
    .add_local_file("config/mn.json", "/root/mn/config/mn.json", copy=True)
    .add_local_python_source("mn_uncensored")
)
state = modal.Dict.from_name(settings.state_dict, create_if_missing=True)
backend_proxy = modal.Secret.from_name("nuri-backend-proxy")
app = modal.App(APP_NAME)


@app.function(
    image=image,
    secrets=[backend_proxy],
    timeout=2 * 60 * 60,
    scaledown_window=60,
    min_containers=0,
    max_containers=2,
)
@modal.concurrent(max_inputs=100, target_inputs=20)
@modal.asgi_app()
def api():
    from mn_uncensored.gateway import create_app

    return create_app(
        state=state,
        models=catalog,
        default_model=settings.default_model,
        proxy_key=os.environ["MODAL_PROXY_KEY"],
        proxy_secret=os.environ["MODAL_PROXY_SECRET"],
    )
