from __future__ import annotations

import hashlib
import secrets


TOKEN_PREFIX = "sk-mn-"


def generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_key(token: str) -> str:
    return f"token:{token_digest(token)}"


def name_key(name: str) -> str:
    return f"name:{name.strip().lower()}"
