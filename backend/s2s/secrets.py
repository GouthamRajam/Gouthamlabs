"""Server-side secret store (MASTER_SPEC Part 28.5), thin Phase 0 version.

Each secret is a JSON document encrypted with Fernet (AES-128-CBC + HMAC-SHA256) and written to
`<S2S_SECRETS_DIR>/<name>.enc` with mode 0600. The encryption key comes from S2S_SECRETS_KEY when
set (the place for a KMS- or vault-provided key); otherwise it is generated once into
`<S2S_SECRETS_DIR>/master.key` (0600). The directory is outside git (.gitignore: var/) and, under
docker compose, a named volume shared only by the backend services.

Plaintext exists only in this process's memory while a secret is being used. Nothing here logs
or prints secret values, and errors never include them.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from s2s.config import REPO_ROOT


def secrets_dir() -> Path:
    return Path(os.environ.get("S2S_SECRETS_DIR", REPO_ROOT / "var" / "secrets"))


def _write_private(path: Path, data: bytes) -> None:
    """Write atomically with mode 0600 (never readable by other users, even briefly)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _fernet() -> Fernet:
    env_key = os.environ.get("S2S_SECRETS_KEY")
    if env_key:
        return Fernet(env_key.encode())
    d = secrets_dir()
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    key_path = d / "master.key"
    if not key_path.exists():
        _write_private(key_path, Fernet.generate_key())
    return Fernet(key_path.read_bytes().strip())


class SecretUnreadable(RuntimeError):
    """The stored secret cannot be decrypted (wrong or replaced key)."""


def put(name: str, value: dict) -> None:
    d = secrets_dir()
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    _write_private(d / f"{name}.enc", _fernet().encrypt(json.dumps(value).encode()))


def get(name: str) -> dict | None:
    path = secrets_dir() / f"{name}.enc"
    if not path.exists():
        return None
    try:
        return json.loads(_fernet().decrypt(path.read_bytes()))
    except InvalidToken:
        raise SecretUnreadable(f"secret '{name}' cannot be decrypted with the current key") from None
