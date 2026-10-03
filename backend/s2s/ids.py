"""Time-sortable ids: <prefix>_<ULID> (48-bit ms timestamp + 80 random bits, Crockford base32).

Monotonic within a process: ids created in the same millisecond still sort in creation
order (the random part is incremented), as in the ULID spec.
"""
from __future__ import annotations

import os
import threading
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_lock = threading.Lock()
_last = 0


def ulid() -> str:
    global _last
    with _lock:
        value = (int(time.time() * 1000) << 80) | int.from_bytes(os.urandom(10), "big")
        if value <= _last:
            value = _last + 1
        _last = value
    return "".join(_ALPHABET[(value >> (5 * i)) & 31] for i in reversed(range(26)))


def new_id(prefix: str) -> str:
    return f"{prefix}_{ulid()}"
