from __future__ import annotations

import hashlib
import base64
import math
import secrets
from slugify import slugify


def ha_slugify(name: str) -> str:
    """ASCII transliterate, lowercase, allow [a-z0-9_], collapse/trim underscores."""
    s = slugify(name, lowercase=True, separator="_", regex_pattern=r"[^a-z0-9_]+")
    s = s.strip("_")
    return s


def get_default_entity_id(platform, device_name, entity_name):
    device_name, entity_name = ha_slugify(device_name), ha_slugify(entity_name)
    while len(f"{platform}.{device_name}_{entity_name}") > 255 and len(device_name) > 20:
        device_name = device_name[:-1]
    return f"{platform}.{device_name}_{entity_name}"[:255]


def build_identifier(seed: str, length: int = 32, namespace: str | None = None) -> str:
    """
    Deterministic, url-safe ID derived from 'seed' and optional 'namespace' (salt).
    Use for Home Assistant unique_id / device identifiers.

    - Output alphabet: [A-Za-z0-9-_]
    - Length: exact 'length'
    - If 'namespace' is provided, it is combined with the seed using a non-printable
      separator to avoid accidental collisions with user content.
    """
    if length < 1:
        raise ValueError("length must be >= 1")
    if len(seed.strip()) < 0 or (namespace is not None and len(namespace.strip()) < 0):
        raise ValueError("seed and namespace must be non-empty")

    if namespace is not None:
        # Use ASCII Unit Separator to avoid collisions with normal text concatenations.
        seed = f"{namespace}\x1f{seed}"

    seed_norm = seed.strip()
    # Ensure enough hash bytes to cover base64 url encoding.
    digest_size = max(16, math.ceil(length * 3 / 4))
    raw = hashlib.blake2s(seed_norm.encode("utf-8"), digest_size=digest_size).digest()
    enc = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return enc[:length]


"""def generate_rand_str(length: int = 16) -> str:
    # Uniform URL-safe string, 6 bits per char
    nbytes = (length * 6 + 7) // 8  # integer ceil(length*3/4)
    return base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).rstrip(b"=").decode("ascii")[:length]"""
