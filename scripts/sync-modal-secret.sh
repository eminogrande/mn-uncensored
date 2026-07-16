#!/bin/zsh

set -euo pipefail

repo_dir="${0:A:h:h}"
cd "$repo_dir"

exec "$repo_dir/.venv/bin/python" -c '
import getpass
import subprocess

def read(service):
    return subprocess.run(
        ["security", "find-generic-password", "-s", service, "-w"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

subprocess.run(
    [
        ".venv/bin/modal",
        "secret",
        "create",
        "nuri-backend-proxy",
        "MODAL_PROXY_KEY=" + read("uncensored-modal-key"),
        "MODAL_PROXY_SECRET=" + read("uncensored-modal-secret"),
        "--force",
    ],
    check=True,
)
print("Synced nuri-backend-proxy without writing credentials to disk.")
'
