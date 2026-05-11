"""Unit tests for src/pact/crypto.py — Ed25519 sign/verify."""

from pact.crypto import generate_keypair, sign, verify


def test_generate_keypair_format():
    priv, pub = generate_keypair()
    assert isinstance(priv, str) and isinstance(pub, str)
    assert len(priv) == 64 and len(pub) == 64
    int(priv, 16)
    int(pub, 16)


def test_sign_verify_roundtrip():
    priv, pub = generate_keypair()
    sig = sign("hello pact", priv)
    assert verify("hello pact", sig, pub) is True


def test_verify_rejects_tampered_message():
    priv, pub = generate_keypair()
    sig = sign("original message", priv)
    assert verify("tampered message", sig, pub) is False


def test_verify_rejects_wrong_key():
    priv, _ = generate_keypair()
    _, other_pub = generate_keypair()
    sig = sign("hello", priv)
    assert verify("hello", sig, other_pub) is False
