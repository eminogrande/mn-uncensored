from __future__ import annotations

import json
from pathlib import Path

import pytest

from mn_uncensored.settings import load_settings


def test_catalog_loads_four_unique_models() -> None:
    settings = load_settings()

    assert settings.default_model == "god"
    assert list(settings.models) == ["god", "code", "fast", "ornith397"]
    assert [model.model for model in settings.models.values()] == [
        "mn/god",
        "mn/code",
        "mn/fast",
        "mn/ornith-397b",
    ]
    assert len({model.lifecycle_key for model in settings.models.values()}) == 4
    assert {
        key: (model.context_window, model.max_output_tokens)
        for key, model in settings.models.items()
    } == {
        "god": (131072, 16384),
        "code": (131072, 16384),
        "fast": (131072, 16384),
        "ornith397": (32768, 8192),
    }
    assert settings.models["god"].aliases == ()
    assert list(settings.deployed_models) == [
        "god",
        "code",
        "fast",
        "ornith397",
    ]
    assert settings.models["ornith397"].deployment_enabled is True
    assert settings.models["ornith397"].requires_cost_acknowledgement is True
    assert settings.models["ornith397"].aliases == (
        "nuri/ornith-397b-abliterated",
    )
    assert settings.idle_shutdown_seconds == 300


def test_catalog_rejects_duplicate_aliases(tmp_path) -> None:
    source = Path(__file__).parents[1] / "config" / "mn.json"
    data = json.loads(source.read_text())
    data["models"]["code"]["aliases"] = ["nuri/ornith-397b-abliterated"]
    path = tmp_path / "mn.json"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="duplicated"):
        load_settings(path)


def test_catalog_rejects_missing_default(tmp_path) -> None:
    source = Path(__file__).parents[1] / "config" / "mn.json"
    data = json.loads(source.read_text())
    data["default_model"] = "missing"
    path = tmp_path / "mn.json"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="default_model"):
        load_settings(path)


def test_catalog_rejects_disabled_default(tmp_path) -> None:
    source = Path(__file__).parents[1] / "config" / "mn.json"
    data = json.loads(source.read_text())
    data["models"]["god"]["deployment_enabled"] = False
    path = tmp_path / "mn.json"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="deployment-enabled"):
        load_settings(path)


@pytest.mark.parametrize("idle_seconds", [0, 301])
def test_catalog_rejects_unsafe_idle_shutdown(
    tmp_path,
    idle_seconds: int,
) -> None:
    source = Path(__file__).parents[1] / "config" / "mn.json"
    data = json.loads(source.read_text())
    data["idle_shutdown_seconds"] = idle_seconds
    path = tmp_path / "mn.json"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="between 1 and 300"):
        load_settings(path)
