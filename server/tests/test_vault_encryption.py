import os

from server.crypto_utils import decrypt_text, encrypt_text


def test_vault_encryption_round_trip_without_plaintext_token(monkeypatch):
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-master-key-for-fast-mvp")
    plaintext = "腾讯成本 321，仓位 40%"

    token = encrypt_text(plaintext)

    assert token != plaintext
    assert "腾讯" not in token
    assert "321" not in token
    assert decrypt_text(token) == plaintext


def test_vault_encryption_requires_master_key(monkeypatch):
    monkeypatch.delenv("ADVISOR_MASTER_KEY", raising=False)

    try:
        encrypt_text("secret")
    except RuntimeError as exc:
        assert "ADVISOR_MASTER_KEY" in str(exc)
    else:
        raise AssertionError("encryption should require ADVISOR_MASTER_KEY")
