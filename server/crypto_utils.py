from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from .config import get_settings


def _derive_key(master_key: str) -> bytes:
    digest = hashlib.sha256(master_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    settings = get_settings()
    if not settings.advisor_master_key:
        raise RuntimeError("ADVISOR_MASTER_KEY is required for encryption.")
    return Fernet(_derive_key(settings.advisor_master_key))


def encrypt_text(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(token: str) -> str:
    return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
