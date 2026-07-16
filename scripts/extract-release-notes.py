from __future__ import annotations

import argparse
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"
VERSION_PATTERN = re.compile(r"^v?(\d+\.\d+\.\d+)$")


def extract_release_notes(changelog: str, version: str) -> str:
    match = VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError("Version must look like v1.2.3.")
    normalized = match.group(1)
    heading = re.compile(
        rf"^## \[{re.escape(normalized)}\](?: - .+)?$",
        re.MULTILINE,
    )
    start_match = heading.search(changelog)
    if start_match is None:
        raise ValueError(f"CHANGELOG.md has no section for {normalized}.")
    content_start = start_match.end()
    next_heading = re.search(r"^## \[", changelog[content_start:], re.MULTILINE)
    content_end = (
        content_start + next_heading.start()
        if next_heading is not None
        else len(changelog)
    )
    notes = changelog[content_start:content_end].strip()
    if not notes:
        raise ValueError(f"CHANGELOG.md section {normalized} is empty.")
    return notes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract one curated release section from CHANGELOG.md.",
    )
    parser.add_argument("version")
    args = parser.parse_args()
    print(extract_release_notes(CHANGELOG_PATH.read_text(), args.version))


if __name__ == "__main__":
    main()
