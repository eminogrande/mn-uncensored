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
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

import httpx
import modal

from .security import generate_token, name_key, token_digest, token_key
from .settings import PROJECT_ROOT, Settings, load_settings


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


def set_desired_state(state: modal.Dict, value: str) -> None:
    state.put("desired_state", value)
    state.put("state_updated_at", datetime.now(UTC).isoformat())


def command_start(args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    current = state.get("desired_state", "stopped")
    if current == "started":
        print("MN Uncensored is marked as started; verifying the backend.")

    print(
        "Starting MN Uncensored on 2 x H200 "
        f"(approximately ${settings.gpu_hourly_usd:.2f}/active hour)..."
    )
    set_desired_state(state, "starting")
    server = modal.Server.from_name(settings.app_name, settings.server_name)
    try:
        server.update_autoscaler(
            target_concurrency=1,
            min_containers=1,
            max_containers=1,
            scaledown_window=300,
        )
    except Exception:
        set_desired_state(state, "stopped")
        raise

    timeout_seconds = args.timeout * 60
    deadline = time.monotonic() + timeout_seconds
    started_at = time.monotonic()
    last_reported_minute = -1
    headers = backend_headers()

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        while time.monotonic() < deadline:
            elapsed = time.monotonic() - started_at
            try:
                response = client.get(f"{settings.backend_url}/health", headers=headers)
            except httpx.HTTPError:
                response = None

            if response is not None and response.status_code == 200:
                set_desired_state(state, "started")
                print(f"Ready after {elapsed / 60:.1f} minutes.")
                print_api_details(settings)
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
        f"The model is still starting after {args.timeout} minutes. "
        "It remains billable; run `mn status` or `mn stop`."
    )


def command_stop(_args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    set_desired_state(state, "stopping")
    server = modal.Server.from_name(settings.app_name, settings.server_name)
    try:
        server.update_autoscaler(
            target_concurrency=1,
            min_containers=0,
            max_containers=1,
            scaledown_window=2,
        )
    except Exception:
        set_desired_state(state, "started")
        raise
    set_desired_state(state, "stopped")
    print("Stopped accepting API requests.")
    print("The H200 pair is scaling down now; no client can wake it through the gateway.")


def command_status(_args: argparse.Namespace, settings: Settings) -> None:
    state = state_dict(settings)
    desired_state = state.get("desired_state", "stopped")
    updated_at = state.get("state_updated_at", "unknown")
    print(f"State: {desired_state}")
    print(f"Model: {settings.model}")
    print(f"Last change: {updated_at}")
    print(f"GPU ceiling: 1 pair (2 x H200, ~${settings.gpu_hourly_usd:.2f}/hour)")

    if desired_state == "started":
        try:
            response = httpx.get(
                f"{settings.backend_url}/health",
                headers=backend_headers(),
                timeout=30,
                follow_redirects=True,
            )
            print(f"Backend health: HTTP {response.status_code}")
        except httpx.HTTPError as error:
            print(f"Backend health: unavailable ({error.__class__.__name__})")

    if settings.api_base_url:
        print(f"API base URL: {settings.api_base_url}")
    else:
        print("API base URL: not deployed yet")


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


def owner_token() -> str:
    from_environment = os.getenv("MN_API_TOKEN", "").strip()
    if from_environment:
        return from_environment
    return keychain_password(OWNER_KEYCHAIN_SERVICE)


def require_ready(settings: Settings) -> None:
    if not settings.api_base_url:
        fail("The API gateway has not been deployed yet.")
    desired_state = state_dict(settings).get("desired_state", "stopped")
    if desired_state != "started":
        fail(f"MN Uncensored is `{desired_state}`. Run `mn start` first.")


def exec_tool(command: list[str], environment: dict[str, str]) -> NoReturn:
    executable = shutil.which(command[0])
    if not executable:
        fail(f"`{command[0]}` is not installed or not on PATH.")
    command[0] = executable
    os.execvpe(executable, command, environment)
    raise AssertionError("execvpe returned unexpectedly")


def launch_hermes(args: list[str], settings: Settings, token: str) -> NoReturn:
    environment = os.environ.copy()
    environment.update(
        {
            "OPENAI_API_KEY": token,
            "OPENAI_BASE_URL": settings.api_base_url,
        }
    )
    exec_tool(
        [
            "hermes",
            "--provider",
            "custom",
            "--model",
            settings.model,
            "--tui",
            *args,
        ],
        environment,
    )


def launch_pi(args: list[str], settings: Settings, token: str) -> NoReturn:
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
            settings.model,
            *args,
        ],
        environment,
    )


def launch_opencode(args: list[str], settings: Settings, token: str) -> NoReturn:
    provider_model = f"mn/{settings.model}"
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
                    settings.model: {
                        "name": "MN Ornith 397B Abliterated",
                        "limit": {"context": 32768, "output": 8192},
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
    require_ready(settings)
    token = owner_token()
    launchers = {
        "hermes": launch_hermes,
        "pi": launch_pi,
        "opencode": launch_opencode,
    }
    launchers[args.tool](args.tool_args, settings, token)


def print_api_details(settings: Settings) -> None:
    if not settings.api_base_url:
        print("Gateway: not deployed yet")
        return
    print(f"Base URL: {settings.api_base_url}")
    print(f"Model:    {settings.model}")
    print("API key:  use the token from `mn token create <name>`")


def command_api(_args: argparse.Namespace, settings: Settings) -> None:
    print_api_details(settings)


def interactive_menu(settings: Settings) -> None:
    while True:
        desired_state = state_dict(settings).get("desired_state", "stopped")
        print()
        print("MN Uncensored")
        print(f"Model state: {desired_state}")
        print("1. Start")
        print("2. Stop")
        print("3. Status")
        print("4. Launch Hermes")
        print("5. Launch Pi")
        print("6. Launch OpenCode")
        print("7. Create API token")
        print("8. Revoke API token")
        print("9. Show API details")
        print("0. Exit")
        choice = input("> ").strip()

        if choice == "0":
            return
        if choice == "1":
            command_start(argparse.Namespace(timeout=90), settings)
        elif choice == "2":
            command_stop(argparse.Namespace(), settings)
        elif choice == "3":
            command_status(argparse.Namespace(), settings)
        elif choice in {"4", "5", "6"}:
            tool = {"4": "hermes", "5": "pi", "6": "opencode"}[choice]
            command_launch(
                argparse.Namespace(tool=tool, tool_args=[]),
                settings,
            )
        elif choice == "7":
            name = input("Token name: ").strip()
            command_token_create(argparse.Namespace(name=name), settings)
        elif choice == "8":
            name = input("Token name: ").strip()
            command_token_revoke(argparse.Namespace(name=name), settings)
        elif choice == "9":
            command_api(argparse.Namespace(), settings)
        else:
            print("Unknown choice.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mn",
        description="Start, stop, and use MN Uncensored.",
    )
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start the H200 model")
    start_parser.add_argument(
        "--timeout",
        type=int,
        default=START_TIMEOUT_SECONDS // 60,
        help="Minutes to wait for the model (default: 90)",
    )

    subparsers.add_parser("stop", help="Stop accepting traffic and scale GPUs down")
    subparsers.add_parser("status", help="Show model and endpoint status")
    subparsers.add_parser("api", help="Show OpenAI-compatible API settings")

    token_parser = subparsers.add_parser("token", help="Manage Bearer API tokens")
    token_subparsers = token_parser.add_subparsers(dest="token_command", required=True)
    token_create = token_subparsers.add_parser("create")
    token_create.add_argument("name")
    token_revoke = token_subparsers.add_parser("revoke")
    token_revoke.add_argument("name")
    token_subparsers.add_parser("list")

    launch_parser = subparsers.add_parser("launch", help="Launch an agent using MN")
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
    elif args.command == "status":
        command_status(args, settings)
    elif args.command == "api":
        command_api(args, settings)
    elif args.command == "token":
        {
            "create": command_token_create,
            "revoke": command_token_revoke,
            "list": command_token_list,
        }[args.token_command](args, settings)
    elif args.command == "launch":
        command_launch(args, settings)


if __name__ == "__main__":
    main()
