from __future__ import annotations

import os

import modal


APP_NAME = "mn-uncensored-api"
STATE_DICT_NAME = "nuri-api-state"
BACKEND_URL = (
    "https://eminhenri--nuri-ornith-397b-vllmserver.eu-west.modal.direct"
)
CONTEXT_WINDOW = 65536
MAX_OUTPUT_TOKENS = 8192
MODEL = "nuri/ornith-397b-abliterated"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("fastapi>=0.128,<0.129", "httpx>=0.28,<1")
    .add_local_python_source("mn_uncensored")
)
state = modal.Dict.from_name(STATE_DICT_NAME, create_if_missing=True)
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
        backend_url=BACKEND_URL,
        context_window=CONTEXT_WINDOW,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        model=MODEL,
        proxy_key=os.environ["MODAL_PROXY_KEY"],
        proxy_secret=os.environ["MODAL_PROXY_SECRET"],
    )
