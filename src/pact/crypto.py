"""Ed25519 signing utilities using PyNaCl."""

from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError


def generate_keypair() -> tuple[str, str]:
    """Generate an Ed25519 keypair. Returns (private_key_hex, public_key_hex)."""
    sk = SigningKey.generate()
    return (
        sk.encode(encoder=HexEncoder).decode(),
        sk.verify_key.encode(encoder=HexEncoder).decode(),
    )


def sign(message: str, private_key_hex: str) -> str:
    """Sign a message with a private key. Returns signature hex."""
    sk = SigningKey(private_key_hex.encode(), encoder=HexEncoder)
    signed = sk.sign(message.encode(), encoder=HexEncoder)
    return signed.signature.decode()


def verify(message: str, signature_hex: str, public_key_hex: str) -> bool:
    """Verify a signature against a message and public key."""
    vk = VerifyKey(public_key_hex.encode(), encoder=HexEncoder)
    try:
        vk.verify(message.encode(), bytes.fromhex(signature_hex))
        return True
    except BadSignatureError:
        return False
