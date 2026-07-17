from __future__ import annotations

from pathlib import Path

from mn_uncensored.security import TOKEN_PREFIX, generate_token, name_key, token_key


def test_generated_tokens_are_unique_and_prefixed() -> None:
    first = generate_token()
    second = generate_token()
    assert first.startswith(TOKEN_PREFIX)
    assert second.startswith(TOKEN_PREFIX)
    assert first != second


def test_storage_key_does_not_contain_plaintext_token() -> None:
    token = generate_token()
    storage_key = token_key(token)
    assert token not in storage_key
    assert storage_key.startswith("token:")


def test_token_names_are_normalized() -> None:
    assert name_key(" Friend-One ") == "name:friend-one"


def test_release_workflow_finishes_with_every_model_stopped() -> None:
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "deploy-release.sh"
    ).read_text()

    assert '.venv/bin/mn auto "$model"' in script
    assert '.venv/bin/mn stop "$model"' in script
    assert "\n.venv/bin/mn auto\n" not in script


def test_release_workflow_fails_closed_before_any_deployment() -> None:
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "deploy-release.sh"
    ).read_text()

    policy_check = script.index('models["ornith397"].deployment_enabled')
    strict_stop = script.index(".venv/bin/mn stop\n", policy_check)
    first_deploy = script.index("deploy_backend qwen36")

    assert policy_check < strict_stop < first_deploy
    assert "MN_RELEASE_ORNITH397=I_ACCEPT_2XH200" in script
    assert "deploy_backend ornith35" in script
    assert "deploy_backend qwythos9" in script
    assert "deploy_backend ornith397" in script
