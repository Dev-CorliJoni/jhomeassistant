from __future__ import annotations

from slugify import slugify

from jhomeassistant.types import Component


def ha_slugify(name: str) -> str:
    """ASCII transliterate, lowercase, allow [a-z0-9_], collapse/trim underscores."""
    s = slugify(name, lowercase=True, separator="_", regex_pattern=r"[^a-z0-9_]+")
    s = s.strip("_")
    return s


def get_default_entity_id(component: Component, device_name, entity_name):
    device_name, entity_name = ha_slugify(device_name), ha_slugify(entity_name)
    while len(f"{component.value}.{device_name}_{entity_name}") > 255 and len(device_name) > 20:
        device_name = device_name[:-1]
    return f"{component.value}.{device_name}_{entity_name}"[:255]
