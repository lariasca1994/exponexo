import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _derive_aes_key() -> bytes:
    raw = get_settings().mfa_encryption_key
    if not raw:
        return hashlib.sha256(b"exponexo-dev-mfa-fallback-key").digest()
    try:
        decoded = base64.urlsafe_b64decode(raw + "===")
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    return hashlib.sha256(raw.encode("utf-8")).digest()


def encrypt_secret(plaintext: str) -> str:
    aesgcm = AESGCM(_derive_aes_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_secret(encrypted: str) -> str:
    aesgcm = AESGCM(_derive_aes_key())
    raw = base64.urlsafe_b64decode(encrypted.encode("ascii"))
    nonce, ciphertext = raw[:12], raw[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
