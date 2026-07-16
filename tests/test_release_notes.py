from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "extract-release-notes.py"
)
SPEC = importlib.util.spec_from_file_location("extract_release_notes", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_extract_release_notes() -> None:
    changelog = """# Changelog

## [Unreleased]

## [1.2.3] - 2026-07-16

### Added

- Detailed notes.

## [1.2.2] - 2026-07-15

- Older notes.
"""

    assert MODULE.extract_release_notes(changelog, "v1.2.3") == (
        "### Added\n\n- Detailed notes."
    )


def test_extract_release_notes_requires_existing_nonempty_section() -> None:
    with pytest.raises(ValueError, match="no section"):
        MODULE.extract_release_notes("## [1.0.0]\n\n- Existing.", "v2.0.0")

    with pytest.raises(ValueError, match="is empty"):
        MODULE.extract_release_notes(
            "## [2.0.0]\n\n## [1.0.0]\n\n- Existing.",
            "v2.0.0",
        )
