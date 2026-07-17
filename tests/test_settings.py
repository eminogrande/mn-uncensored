from __future__ import annotations

import json
from pathlib import Path

import pytest

from mn_uncensored.settings import load_settings


def test_catalog_loads_four_unique_models() -> None:
    settings = load_settings()

    assert settings.default_model == "qwen36"
    assert list(settings.models) == ["qwen36", "ornith35", "qwythos9", "ornith397"]
    assert [model.model for model in settings.models.values()] == [
        "huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated",
        "YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated",
        "huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated",
        "cebeuq/Ornith-1.0-397B-abliterated-W4A16",
    ]
    assert len({model.lifecycle_key for model in settings.models.values()}) == 4
    assert {
        key: (model.context_window, model.max_output_tokens)
        for key, model in settings.models.items()
    } == {
        "qwen36": (131072, 16384),
        "ornith35": (131072, 16384),
        "qwythos9": (131072, 16384),
        "ornith397": (32768, 8192),
    }
    assert settings.models["qwen36"].aliases == ("mn/god",)
    assert list(settings.deployed_models) == [
        "qwen36",
        "ornith35",
        "qwythos9",
    ]
    assert settings.models["ornith397"].deployment_enabled is False
    assert settings.models["ornith397"].requires_cost_acknowledgement is True
    assert settings.models["ornith397"].aliases == (
        "mn/ornith-397b",
        "nuri/ornith-397b-abliterated",
    )
    assert all(
        model.model == model.hf_model
        for model in settings.models.values()
    )
    assert settings.idle_shutdown_seconds == 300


def test_modal_app_names_use_model_names_not_role_labels() -> None:
    settings = load_settings()

    assert {
        key: model.app_name for key, model in settings.models.items()
    } == {
        "qwen36": "huihui-qwen3-6-35b-a3b-abliterated",
        "ornith35": "yuyu1015-ornith-1-0-35b-abliterated",
        "qwythos9": "huihui-qwythos-9b-claude-mythos-5-1m-abliterated",
        "ornith397": "cebeuq-ornith-1-0-397b-abliterated-w4a16",
    }
    assert all(
        role not in model.app_name
        for model in settings.models.values()
        for role in ("-god-", "-code-", "-fast-")
    )


def test_catalog_rejects_duplicate_aliases(tmp_path) -> None:
    source = Path(__file__).parents[1] / "config" / "mn.json"
    data = json.loads(source.read_text())
    data["models"]["ornith35"]["aliases"] = ["nuri/ornith-397b-abliterated"]
    path = tmp_path / "mn.json"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="duplicated"):
        load_settings(path)


def test_catalog_rejects_public_id_that_is_not_exact_hf_id(tmp_path) -> None:
    source = Path(__file__).parents[1] / "config" / "mn.json"
    data = json.loads(source.read_text())
    data["models"]["qwen36"]["model"] = "mn/not-the-real-model"
    path = tmp_path / "mn.json"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="exact Hugging Face model ID"):
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
    data["models"]["qwen36"]["deployment_enabled"] = False
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
