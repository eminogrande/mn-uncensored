from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from typing import NoReturn

import httpx
import modal

from .security import generate_token, name_key, token_digest, token_key
from .settings import ModelSettings, PROJECT_ROOT, Settings, load_settings


OWNER_KEYCHAIN_SERVICE = "mn-uncensored-owner-token"
PROXY_KEY_SERVICE = "uncensored-modal-key"
PROXY_SECRET_SERVICE = "uncensored-modal-secret"
TOKEN_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
START_TIMEOUT_SECONDS = 90 * 60


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def keychain_password(service: str) -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-w"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail(f"Keychain entry `{service}` was not found.")
    return result.stdout.strip()


def store_keychain_password(service: str, password: str) -> None:
    result = subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-a",
            getpass.getuser(),
            "-s",
            service,
            "-w",
            password,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail(f"Could not store `{service}` in the macOS Keychain.")


def state_dict(settings: Settings) -> modal.Dict:
    return modal.Dict.from_name(settings.state_dict, create_if_missing=True)


def backend_headers() -> dict[str, str]:
    return {
        "Modal-Key": keychain_password(PROXY_KEY_SERVICE),
        "Modal-Secret": keychain_password(PROXY_SECRET_SERVICE),
    }


def model_lifecycle(
    state: modal.Dict,
    model: ModelSettings,
    settings: Settings,
) -> dict[str, object]:
    record = state.get(model.lifecycle_key)
    if isinstance(record, dict) and "desired_state" in record:
        return record
    if model.key == settings.default_model:
        return {
            "schema": 0,
            "desired_state": state.get("desired_state", "stopped"),
            "updated_at": state.get("state_updated_at", "unknown"),
        }
    return {
        "schema": 1,
        "desired_state": "stopped",
        "updated_at": "unknown",
    }


def set_desired_state(
    state: modal.Dict,
    model: ModelSettings,
    settings: Settings,
    value: str,
    *,
    operation_id: str | None = None,
) -> None:
    updated_at = datetime.now(UTC).isoformat()
    record: dict[str, object] = {
        "schema": 1,
        "desired_state": value,
        "updated_at": updated_at,
    }
    if operation_id is not None:
        record["operation_id"] = operation_id
    state.put(
        model.lifecycle_key,
        record,
    )
    if model.key == settings.default_model:
        state.put("desired_state", value)
        state.put("state_updated_at", updated_at)


def resolve_model(settings: Settings, value: str | None) -> ModelSettings:
    try:
        return settings.resolve_model(value)
    except ValueError as error:
        fail(str(error))


def resolve_models(
    settings: Settings,
    value: str | None,
    *,
    default_all: bool,
) -> list[ModelSettings]:
    candidate = value or ("all" if default_all else settings.default_model)
    if candidate == "all":
        return list(settings.models.values())
    return [resolve_model(settings, candidate)]


def modal_cli_path() -> str:
    project_cli = PROJECT_ROOT / ".venv" / "bin" / "modal"
    if project_cli.exists():
        return str(project_cli)
    executable = shutil.which("modal")
    if not executable:
        fail("The Modal CLI is not installed or not on PATH.")
    return executable


def backend_app_is_stopped(model: ModelSettings) -> bool:
    result = subprocess.run(
        [modal_cli_path(), "app", "list", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        apps = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    for app in apps:
        if app.get("description") == model.app_name:
            return app.get("state") == "stopped"
    return True


def reset_backend_to_static(model: ModelSettings) -> None:
    command = [
        modal_cli_path(),
        "app",
        "rollover",
        model.app_name,
        "--strategy",
        "recreate",
    ]
    for attempt in range(2):
        result = subprocess.run(command, check=False)
        if result.returncode == 0:
            return
        if attempt == 0:
            print(
                f"Modal did not finish stopping `{model.key}`; retrying once.",
                file=sys.stderr,
            )
            time.sleep(3)
    fail(
        f"Could not reset backend `{model.key}`; its gateway route remains fail-closed."
    )


def deploy_backend(model: ModelSettings, tag: str) -> None:
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if status_result.returncode != 0 or status_result.stdout.strip():
        fail("Backend recovery deploy requires a clean Git working tree.")
    signature_result = subprocess.run(
        ["git", "log", "-1", "--format=%G?"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if signature_result.returncode != 0 or signature_result.stdout.strip() != "G":
        fail("Backend recovery deploy requires a verified signed HEAD commit.")
    commit_result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    environment = os.environ.copy()
    environment["MN_MODEL"] = model.key
    deployment_tag = f"{tag}-{model.key}-{commit_result.stdout.strip()}"
    result = subprocess.run(
        [
            modal_cli_path(),
            "deploy",
            str(PROJECT_ROOT / "modal_vllm.py"),
            "--tag",
            deployment_tag,
        ],
        check=False,
        env=environment,
    )
    if result.returncode != 0:
        fail(
            f"Could not deploy the `{model.key}` scale-to-zero backend; state remains stopped."
        )


def start_model(
    args: argparse.Namespace,
    settings: Settings,
    model: ModelSettings,
) -> None:
    state = state_dict(settings)
    current = str(
        model_lifecycle(state, model, settings).get("desired_state", "stopped")
    )
    if current == "started":
        print(f"{model.model} is marked as started; verifying the backend.")

    operation_id = uuid.uuid4().hex

    def start_is_current() -> bool:
        record = model_lifecycle(state, model, settings)
        return (
            record.get("desired_state") == "starting"
            and record.get("operation_id") == operation_id
        )

    print(
        f"Starting {model.model} on {model.gpu_label} "
        f"(approximately ${model.gpu_hourly_usd:.2f}/active hour)..."
    )
    set_desired_state(
        state,
        model,
        settings,
        "starting",
        operation_id=operation_id,
    )
    if backend_app_is_stopped(model):
        try:
            deploy_backend(model, "manual-start")
        except SystemExit:
            if start_is_current():
                set_desired_state(state, model, settings, "stopped")
            raise
        if not start_is_current():
            print(f"Start canceled while deploying {model.model}.")
            return
    server = modal.Server.from_name(model.app_name, model.server_name)
    try:
        server.update_autoscaler(
            min_containers=1,
            max_containers=1,
            scaledown_window=300,
        )
    except Exception:
        if start_is_current():
            set_desired_state(state, model, settings, current)
        raise

    timeout_seconds = args.timeout * 60
    deadline = time.monotonic() + timeout_seconds
    started_at = time.monotonic()
    last_reported_minute = -1
    headers = backend_headers()

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        while time.monotonic() < deadline:
            if not start_is_current():
                print(
                    f"Start canceled because {model.model} lifecycle changed."
                )
                return
            elapsed = time.monotonic() - started_at
            try:
                response = client.get(f"{model.backend_url}/health", headers=headers)
            except httpx.HTTPError:
                response = None

            if response is not None and response.status_code == 200:
                if not start_is_current():
                    print(
                        f"Start canceled because {model.model} lifecycle changed."
                    )
                    return
                set_desired_state(state, model, settings, "started")
                print(f"{model.model} ready after {elapsed / 60:.1f} minutes.")
                print_api_details(settings, model)
                return
            if response is not None and response.status_code not in {502, 503, 504}:
                print(
                    f"Backend health check returned HTTP {response.status_code}; retrying.",
                    file=sys.stderr,
                )

            elapsed_minute = int(elapsed // 60)
            if elapsed_minute != last_reported_minute:
                print(f"Still starting... {elapsed_minute} minute(s) elapsed")
                last_reported_minute = elapsed_minute
            time.sleep(5)

    fail(
        f"{model.model} is still starting after {args.timeout} minutes. "
        f"It remains billable; run `mn status {model.key}` or `mn stop {model.key}`."
    )


def command_start(args: argparse.Namespace, settings: Settings) -> None:
    start_model(args, settings, resolve_model(settings, args.model))


def command_stop(args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    for model in resolve_models(settings, args.model, default_all=True):
        if backend_app_is_stopped(model):
            set_desired_state(state, model, settings, "stopped")
            print(f"{model.model} is already hard-stopped.")
            continue
        set_desired_state(state, model, settings, "stopping")
        reset_backend_to_static(model)
        set_desired_state(state, model, settings, "stopped")
        print(f"Stopped {model.model}; its backend is at static scale-to-zero.")


def command_auto(args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    for model in resolve_models(settings, args.model, default_all=True):
        operation_id = uuid.uuid4().hex

        def operation_is_current() -> bool:
            return (
                model_lifecycle(state, model, settings).get("operation_id")
                == operation_id
            )

        previous_state = str(
            model_lifecycle(state, model, settings).get(
                "desired_state",
                "stopped",
            )
        )
        if backend_app_is_stopped(model):
            set_desired_state(
                state,
                model,
                settings,
                "stopped",
                operation_id=operation_id,
            )
            try:
                deploy_backend(model, "auto-lifecycle")
            except SystemExit:
                if operation_is_current():
                    set_desired_state(state, model, settings, "stopped")
                raise
        elif previous_state in {"started", "starting", "stopping"}:
            set_desired_state(
                state,
                model,
                settings,
                "stopping",
                operation_id=operation_id,
            )
            reset_backend_to_static(model)
        else:
            set_desired_state(
                state,
                model,
                settings,
                previous_state,
                operation_id=operation_id,
            )
        if not operation_is_current():
            print(f"Auto canceled because {model.model} lifecycle changed.")
            continue
        set_desired_state(state, model, settings, "auto")
        print(
            f"Auto enabled for {model.model}: wake on request, scale to zero after "
            f"{settings.idle_shutdown_seconds // 60} idle minutes."
        )


def command_status(args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    selected = resolve_models(settings, args.model, default_all=True)
    for index, model in enumerate(selected):
        if index:
            print()
        record = model_lifecycle(state, model, settings)
        desired_state = str(record.get("desired_state", "stopped"))
        print(f"Model: {model.model} ({model.key})")
        print(f"Name: {model.display_name}")
        print(f"State: {desired_state}")
        print(f"Last change: {record.get('updated_at', 'unknown')}")
        print(
            f"GPU ceiling: {model.gpu_label}, "
            f"~${model.gpu_hourly_usd:.2f}/active hour"
        )
        print(
            f"Context: {model.context_window:,} tokens; "
            f"idle shutdown: {settings.idle_shutdown_seconds // 60} minutes"
        )

        if desired_state == "started":
            try:
                response = httpx.get(
                    f"{model.backend_url}/health",
                    headers=backend_headers(),
                    timeout=30,
                    follow_redirects=True,
                )
                print(f"Backend health: HTTP {response.status_code}")
            except httpx.HTTPError as error:
                print(f"Backend health: unavailable ({error.__class__.__name__})")
    print()
    print(
        f"API base URL: {settings.api_base_url or 'not deployed yet'}"
    )


def validate_token_name(name: str) -> str:
    if not TOKEN_NAME_PATTERN.fullmatch(name):
        fail(
            "Token names must be 1-64 characters using letters, numbers, dot, "
            "underscore, or hyphen."
        )
    return name.lower()


def command_token_create(args: argparse.Namespace, settings: Settings) -> None:
    name = validate_token_name(args.name)
    state = state_dict(settings)
    if state.get(name_key(name)):
        fail(f"A token named `{name}` already exists. Revoke it first.")

    token = generate_token()
    digest = token_digest(token)
    metadata = {
        "active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "name": name,
    }

    if name == "owner":
        store_keychain_password(OWNER_KEYCHAIN_SERVICE, token)
    state.put(token_key(token), metadata)
    state.put(name_key(name), {"digest": digest, **metadata})

    if name == "owner":
        print("Owner token created and stored in the macOS Keychain.")
    else:
        print("Token created. Copy it now; MN does not store its plaintext locally.")
        print(token)


def command_token_revoke(args: argparse.Namespace, settings: Settings) -> None:
    name = validate_token_name(args.name)
    state = state_dict(settings)
    metadata = state.get(name_key(name))
    if not metadata:
        fail(f"No token named `{name}` exists.")
    state.pop(f"token:{metadata['digest']}", None)
    state.pop(name_key(name), None)
    print(f"Revoked token `{name}`.")


def command_token_list(_args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    entries = sorted(
        (
            value
            for key, value in state.items()
            if isinstance(key, str) and key.startswith("name:")
        ),
        key=lambda item: item["name"],
    )
    if not entries:
        print("No API tokens.")
        return
    for entry in entries:
        print(f"{entry['name']}\tcreated {entry['created_at']}")


def command_token_copy(args: argparse.Namespace, _settings: Settings) -> None:
    name = validate_token_name(args.name)
    if name != "owner":
        fail("Only the locally stored `owner` token can be copied.")
    token = keychain_password(OWNER_KEYCHAIN_SERVICE)
    result = subprocess.run(
        ["pbcopy"],
        input=token,
        text=True,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        fail("Could not copy the owner token to the clipboard.")
    print("Owner token copied to the clipboard.")


def owner_token() -> str:
    from_environment = os.getenv("MN_API_TOKEN", "").strip()
    if from_environment:
        return from_environment
    return keychain_password(OWNER_KEYCHAIN_SERVICE)


def require_launch_allowed(
    settings: Settings,
    model: ModelSettings,
) -> str:
    if not settings.api_base_url:
        fail("The API gateway has not been deployed yet.")
    desired_state = str(
        model_lifecycle(state_dict(settings), model, settings).get(
            "desired_state",
            "stopped",
        )
    )
    if desired_state not in {"auto", "started"}:
        fail(
            f"{model.model} is `{desired_state}`. "
            f"Run `mn auto {model.key}` or `mn start {model.key}` first."
        )
    return desired_state


def wake_model(settings: Settings, model: ModelSettings, token: str) -> None:
    print(
        f"Waking {model.model} if needed; a first download or cold start can take time..."
    )
    try:
        response = httpx.post(
            f"{settings.gateway_url}/wake",
            params={"model": model.model},
            headers={"Authorization": f"Bearer {token}"},
            timeout=45 * 60,
            follow_redirects=True,
        )
    except httpx.HTTPError as error:
        fail(f"Could not wake {model.model} ({error.__class__.__name__}).")
    if response.status_code != 200:
        try:
            message = response.json()["error"]["message"]
        except (KeyError, TypeError, ValueError):
            message = f"HTTP {response.status_code}"
        fail(f"Could not wake {model.model}: {message}")
    print(f"{model.model} ready.")


def command_wake(args: argparse.Namespace, settings: Settings) -> None:
    model = resolve_model(settings, args.model)
    require_launch_allowed(settings, model)
    wake_model(settings, model, owner_token())


def exec_tool(command: list[str], environment: dict[str, str]) -> NoReturn:
    executable = shutil.which(command[0])
    if not executable:
        fail(f"`{command[0]}` is not installed or not on PATH.")
    command[0] = executable
    os.execvpe(executable, command, environment)
    raise AssertionError("execvpe returned unexpectedly")


def launch_hermes(
    args: list[str],
    settings: Settings,
    model: ModelSettings,
    token: str,
) -> NoReturn:
    hermes = shutil.which("hermes")
    if not hermes:
        fail("`hermes` is not installed or not on PATH.")
    provider_values = {
        "api": settings.api_base_url,
        "key_env": "MN_API_TOKEN",
        "transport": "chat_completions",
        "default_model": model.model,
        "context_length": str(model.context_window),
        "request_timeout_seconds": "2700",
        "stale_timeout_seconds": "2700",
    }
    for key, value in provider_values.items():
        result = subprocess.run(
            [
                hermes,
                "config",
                "set",
                f"providers.mn-uncensored.{key}",
                value,
            ],
            check=False,
        )
        if result.returncode != 0:
            fail(f"Could not configure Hermes provider field `{key}`.")

    environment = os.environ.copy()
    environment.update(
        {
            "MN_API_TOKEN": token,
            "HERMES_API_TIMEOUT": "2700",
            "HERMES_STREAM_READ_TIMEOUT": "2700",
            "HERMES_STREAM_STALE_TIMEOUT": "2700",
            "HERMES_API_CALL_STALE_TIMEOUT": "2700",
        }
    )
    exec_tool(
        [
            "hermes",
            "--provider",
            "custom:mn-uncensored",
            "--model",
            model.model,
            "--tui",
            *args,
        ],
        environment,
    )


def launch_pi(
    args: list[str],
    _settings: Settings,
    model: ModelSettings,
    token: str,
) -> NoReturn:
    environment = os.environ.copy()
    environment.update(
        {
            "MN_API_TOKEN": token,
            "PI_CODING_AGENT_DIR": str(PROJECT_ROOT / "config" / "pi-agent"),
        }
    )
    exec_tool(
        [
            "pi",
            "--provider",
            "mn",
            "--model",
            model.model,
            *args,
        ],
        environment,
    )


def launch_opencode(
    args: list[str],
    settings: Settings,
    model: ModelSettings,
    token: str,
) -> NoReturn:
    provider_model = f"mn/{model.key}"
    config = {
        "$schema": "https://opencode.ai/config.json",
        "model": provider_model,
        "provider": {
            "mn": {
                "name": "MN Uncensored",
                "npm": "@ai-sdk/openai-compatible",
                "options": {
                    "apiKey": "{env:MN_API_TOKEN}",
                    "baseURL": settings.api_base_url,
                },
                "models": {
                    model.key: {
                        "name": model.display_name,
                        "limit": {
                            "context": model.context_window,
                            "output": model.max_output_tokens,
                        },
                    }
                },
            }
        },
    }
    environment = os.environ.copy()
    environment.update(
        {
            "MN_API_TOKEN": token,
            "OPENCODE_CONFIG_CONTENT": json.dumps(config),
        }
    )
    exec_tool(["opencode", "-m", provider_model, *args], environment)


def command_launch(args: argparse.Namespace, settings: Settings) -> None:
    model = resolve_model(settings, args.model)
    desired_state = require_launch_allowed(settings, model)
    token = owner_token()
    if desired_state == "auto":
        wake_model(settings, model, token)
    launchers = {
        "hermes": launch_hermes,
        "pi": launch_pi,
        "opencode": launch_opencode,
    }
    launchers[args.tool](args.tool_args, settings, model, token)


def print_api_details(settings: Settings, selected: ModelSettings | None = None) -> None:
    if not settings.api_base_url:
        print("Gateway: not deployed yet")
        return
    print(f"Base URL: {settings.api_base_url}")
    models = [selected] if selected is not None else settings.models.values()
    for model in models:
        print(
            f"Model:    {model.model:<10} {model.display_name} "
            f"({model.context_window:,} context)"
        )
    print("API key:  run `mn token copy owner` or create a named friend token")


def command_api(args: argparse.Namespace, settings: Settings) -> None:
    selected = None if args.model == "all" else resolve_model(settings, args.model)
    print_api_details(settings, selected)


def interactive_menu(settings: Settings) -> None:
    while True:
        print()
        print("MN Uncensored")
        for model in settings.models.values():
            desired_state = model_lifecycle(
                state_dict(settings),
                model,
                settings,
            ).get("desired_state", "stopped")
            print(f"  {model.key:<4} {model.model:<10} {desired_state}")
        print("1. Start one model")
        print("2. Auto mode for all")
        print("3. Stop all")
        print("4. Status")
        print("5. Launch Hermes")
        print("6. Launch Pi")
        print("7. Launch OpenCode")
        print("8. Create API token")
        print("9. Revoke API token")
        print("10. Show API details")
        print("0. Exit")
        choice = input("> ").strip()

        if choice == "0":
            return
        if choice == "1":
            model = input("Model [god/code/fast]: ").strip() or settings.default_model
            command_start(argparse.Namespace(timeout=90, model=model), settings)
        elif choice == "2":
            command_auto(argparse.Namespace(model="all"), settings)
        elif choice == "3":
            command_stop(argparse.Namespace(model="all"), settings)
        elif choice == "4":
            command_status(argparse.Namespace(model="all"), settings)
        elif choice in {"5", "6", "7"}:
            tool = {"5": "hermes", "6": "pi", "7": "opencode"}[choice]
            model = input("Model [god/code/fast]: ").strip() or settings.default_model
            command_launch(
                argparse.Namespace(tool=tool, tool_args=[], model=model),
                settings,
            )
        elif choice == "8":
            name = input("Token name: ").strip()
            command_token_create(argparse.Namespace(name=name), settings)
        elif choice == "9":
            name = input("Token name: ").strip()
            command_token_revoke(argparse.Namespace(name=name), settings)
        elif choice == "10":
            command_api(argparse.Namespace(model="all"), settings)
        else:
            print("Unknown choice.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mn",
        description="Start, stop, and use the MN Uncensored model catalog.",
    )
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start one model and keep it warm")
    start_parser.add_argument("model", nargs="?", default=None)
    start_parser.add_argument(
        "--timeout",
        type=int,
        default=START_TIMEOUT_SECONDS // 60,
        help="Minutes to wait for the model (default: 90)",
    )

    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop one model or all models",
    )
    stop_parser.add_argument("model", nargs="?", default="all")

    auto_parser = subparsers.add_parser(
        "auto",
        help="Wake on request and shut down after idle time",
    )
    auto_parser.add_argument("model", nargs="?", default="all")

    status_parser = subparsers.add_parser("status", help="Show catalog status")
    status_parser.add_argument("model", nargs="?", default="all")

    wake_parser = subparsers.add_parser("wake", help="Wake one model")
    wake_parser.add_argument("model", nargs="?", default=None)

    api_parser = subparsers.add_parser(
        "api",
        help="Show OpenAI-compatible API settings",
    )
    api_parser.add_argument("model", nargs="?", default="all")

    token_parser = subparsers.add_parser("token", help="Manage Bearer API tokens")
    token_subparsers = token_parser.add_subparsers(dest="token_command", required=True)
    token_create = token_subparsers.add_parser("create")
    token_create.add_argument("name")
    token_revoke = token_subparsers.add_parser("revoke")
    token_revoke.add_argument("name")
    token_copy = token_subparsers.add_parser("copy")
    token_copy.add_argument("name")
    token_subparsers.add_parser("list")

    launch_parser = subparsers.add_parser("launch", help="Launch an agent using MN")
    launch_parser.add_argument(
        "--model",
        default=None,
        help="Catalog model: god, code, or fast (place before the tool name)",
    )
    launch_parser.add_argument("tool", choices=["hermes", "pi", "opencode"])
    launch_parser.add_argument("tool_args", nargs=argparse.REMAINDER)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings()

    if args.command is None:
        interactive_menu(settings)
    elif args.command == "start":
        command_start(args, settings)
    elif args.command == "stop":
        command_stop(args, settings)
    elif args.command == "auto":
        command_auto(args, settings)
    elif args.command == "status":
        command_status(args, settings)
    elif args.command == "wake":
        command_wake(args, settings)
    elif args.command == "api":
        command_api(args, settings)
    elif args.command == "token":
        {
            "create": command_token_create,
            "revoke": command_token_revoke,
            "copy": command_token_copy,
            "list": command_token_list,
        }[args.token_command](args, settings)
    elif args.command == "launch":
        command_launch(args, settings)


if __name__ == "__main__":
    main()
