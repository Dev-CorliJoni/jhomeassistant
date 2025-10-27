# Names in English, comments in English.
import hashlib
import base64
import math


def build_identifier(seed: str, length: int = 32) -> str:
    """
    Deterministic, url-safe ID derived from 'seed'.
    Use for Home Assistant unique_id / device identifiers.
    - Output alphabet: [A-Za-z0-9-_]
    - Length: exact 'length'
    """
    if length < 1:
        raise ValueError("length must be >= 1")
    seed_norm = seed.strip()
    # Ensure enough hash bytes to cover base64 url encoding.
    digest_size = max(16, math.ceil(length * 3 / 4))
    raw = hashlib.blake2s(seed_norm.encode("utf-8"), digest_size=digest_size).digest()
    enc = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return enc[:length]
