"""Approval signatures separate decision provenance from executor-writable audit state."""

import base64
import json
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from governed_dataops.contracts import Approval


def approval_bytes(approval: Approval) -> bytes:
    return json.dumps(
        approval.model_dump(mode="json", exclude={"signature"}),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def generate_approval_keys(private_path: str | Path, public_path: str | Path) -> None:
    private_path, public_path = Path(private_path), Path(public_path)
    if private_path.exists() or public_path.exists():
        raise FileExistsError("Refusing to overwrite approval signing keys")
    private_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    public_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = Ed25519PrivateKey.generate()
    descriptor = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    descriptor = os.open(public_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as output:
        output.write(
            key.public_key().public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )


def sign_approval(approval: Approval, private_key_path: str | Path) -> Approval:
    key = serialization.load_pem_private_key(Path(private_key_path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Approval signing requires an Ed25519 private key")
    return approval.model_copy(
        update={"signature": base64.b64encode(key.sign(approval_bytes(approval))).decode()}
    )


def verify_approval_signature(approval: Approval, public_key_path: str | Path) -> bool:
    if not approval.signature or not public_key_path:
        return False
    try:
        key = serialization.load_pem_public_key(Path(public_key_path).read_bytes())
        if not isinstance(key, Ed25519PublicKey):
            return False
        key.verify(base64.b64decode(approval.signature, validate=True), approval_bytes(approval))
    except (OSError, ValueError, InvalidSignature):
        return False
    return True
