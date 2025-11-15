from __future__ import annotations

import re
from typing import List, Tuple, Any
from simplehomeassistant.setup_logging import get_logger
from simplehomeassistant.types.component import Component
from simplehomeassistant.types.device_classes.base_device_class import BaseDeviceClass
from simplehomeassistant.types.units import MonetaryUnit
from simplehomeassistant.types.units.base import BaseUnit

logger = get_logger("validation")


def validate_non_empty_string(value: str | None, field: str, allow_none=False) -> str | None:
    """
    Validate that 'value' is a non-empty string.
    """
    if allow_none and value is None:
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field} is invalid: value must be a string.")
    if value.strip() == "":
        raise ValueError(f"{field} is invalid: value must not be empty.")
    return value


def validate_discovery_prefix(value: str) -> str:
    """
    Validate a Home Assistant MQTT discovery prefix.

    Rules:
    - Non-empty UTF-8 string.
    - Must not start with '$' (avoid $SYS and system namespaces).
    - Must not contain MQTT wildcards '+' or '#'.
    - Must not contain the null character.
    - No leading or trailing whitespace.
    - No empty topic segments (reject '//' or leading/trailing '/').
    - Whitespace inside is rejected to avoid fragile topics.
    """
    validate_non_empty_string(value, "discovery_prefix")
    if value != value.strip():
        raise ValueError("discovery_prefix is invalid: leading or trailing whitespace is not allowed.")
    if value.startswith("$"):
        raise ValueError("discovery_prefix is invalid: must not start with '$'.")
    if "+" in value or "#" in value:
        raise ValueError("discovery_prefix is invalid: wildcards '+' and '#' are not allowed.")
    if "\x00" in value:
        raise ValueError("discovery_prefix is invalid: null character is not allowed.")
    if any(char.isspace() for char in value):
        raise ValueError("discovery_prefix is invalid: whitespace characters are not allowed.")
    if value.startswith("/") or value.endswith("/"):
        raise ValueError("discovery_prefix is invalid: must not start or end with '/'.")
    if "//" in value:
        raise ValueError("discovery_prefix is invalid: empty topic segments are not allowed (no '//').")

    # UTF-8 encodability check
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("discovery_prefix is invalid: must be UTF-8 encodable.")
    return value


# Not necessary :
def _validate_discovery_topic_id(value: str, id_name: str) -> str:
    """
    Validate a Node ID or Object ID for Home Assistant MQTT discovery.

    Rules for both:
    - Only letters, digits, underscore, hyphen: [A-Za-z0-9_-]+
    - No slashes, no spaces, no other symbols.
    - Non-empty.

    Returns the input value if valid.
    Raises ValidationError with a clear reason if invalid.
    """
    validate_non_empty_string(value, id_name)
    if not re.fullmatch(r"^[A-Za-z0-9_-]+$", value):
        raise ValueError(f"{id_name} is invalid: only letters, digits, underscore, and hyphen are allowed.")
    return value


"""def validate_object_id(value: str) -> str:
    return _validate_discovery_topic_id(value, "object_id")


def validate_node_id(value: str | None) -> str | None:
    return value if value is None else _validate_discovery_topic_id(value, "node_id")"""


def validate_topic(topic: str, strict_mode: bool = False) -> str:
    """
    Validate an MQTT topic name.

    Spec-enforced checks (always errors):
      - Non-empty UTF-8 string.
      - No null character ('\\x00').
      - UTF-8 length <= 65535 bytes.
      - No '+' or '#' (wildcards are for filters, not topic names).

    Best-practice checks (warnings by default; errors if strict_mode=True):
      - No leading/trailing whitespace.
      - No internal whitespace.
      - Do not start with '$' (reserved for broker/$SYS).
      - Avoid leading/trailing '/'.
      - Avoid empty levels ('//').

    Returns the topic if valid, else raises ValueError.
    """

    # ---- Spec-enforced ----
    validate_non_empty_string(topic, "topic")
    if "\x00" in topic:
        raise ValueError("topic is invalid: null character is not allowed.")

    try:
        encoded = topic.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("topic is invalid: must be UTF-8 encodable.")

    if len(encoded) > 65535:
        raise ValueError("topic is invalid: UTF-8 length must be ≤ 65535 bytes.")
    if "+" in topic or "#" in topic:
        raise ValueError("topic is invalid: wildcards '+' and '#' are not allowed in topic names.")

    # ---- Best practices (warn or error) ----
    bp_issues = []

    if topic != topic.strip():
        bp_issues.append("leading or trailing whitespace is not recommended.")
    if any(c.isspace() for c in topic):
        bp_issues.append("whitespace inside topic is not recommended.")
    if topic.startswith("$"):
        bp_issues.append("topics starting with '$' are reserved for broker/system.")
    if topic.startswith("/") or topic.endswith("/"):
        bp_issues.append("avoid leading or trailing '/'.")
    if "//" in topic:
        bp_issues.append("avoid empty topic levels ('//').")

    if bp_issues:
        msg = "validate_topic best-practice issues: " + "; ".join(bp_issues)
        if strict_mode:
            logger.error(msg)
            raise ValueError("topic violates best practices: " + "; ".join(bp_issues))
        else:
            logger.warning(msg)

    return topic


def validate_icon(name: str) -> str:
    """
    Validate an MDI icon name like 'mdi:play-circle'.
    Returns the name typed as IconName if valid.
    Raises ValueError on invalid input.
    """
    if not isinstance(name, str) or not re.fullmatch(r"^mdi:[a-z0-9_\-]+$", name):
        raise ValueError("""Icon not valid.
                         Information: https://www.home-assistant.io/docs/frontend/icons/.
                         Allowed icons: https://pictogrammers.com/library/mdi/""")
    return name


def get_entity_spec_help_links(platform: Component | None = None) -> List[str]:
    additional_help = {
        Component.BINARY_SENSOR: "https://www.home-assistant.io/integrations/binary_sensor/#device-class",
        Component.BUTTON: "https://www.home-assistant.io/integrations/button/#device-class",
        Component.COVER: "https://www.home-assistant.io/integrations/cover/#device-class",
        Component.EVENT: "https://www.home-assistant.io/integrations/event/#device-class",
        Component.HUMIDIFIER: "https://www.home-assistant.io/integrations/humidifier/#device-class",
        Component.MEDIA_PLAYER: "https://www.home-assistant.io/integrations/media_player/#device-class",
        Component.NUMBER: "https://www.home-assistant.io/integrations/number/#device-class",
        Component.SENSOR: "https://www.home-assistant.io/integrations/sensor#device-class",
        Component.SWITCH: "https://www.home-assistant.io/integrations/switch/#device-class",
        Component.UPDATE: "https://www.home-assistant.io/integrations/update/#device-class",
        Component.VALVE: "https://www.home-assistant.io/integrations/valve/#device-class"
    }
    help_links = ["https://www.home-assistant.io/integrations/homeassistant/#device-class"]
    if platform in additional_help:
        help_links.append(additional_help[platform])
    return help_links


def _validate_platform(platform: Component, allowed_config) -> Component:
    if platform not in allowed_config:
        allowed_platforms = sorted(allowed_config.keys())
        raise ValueError(f"Unsupported platform '{platform}'. Allowed: {allowed_platforms}. See {get_entity_spec_help_links()}")
    return platform


def validate_entity_specification(
    platform: Component,
    device_class: BaseDeviceClass,
    unit: BaseUnit,
) -> Tuple[Component, Any, Any]:
    """
    Validate a Home Assistant entity specification.

    Returns the normalized (platform, device_class, unit_of_measurement) tuple.

    Rules:
    - Platform must exist in allowed_config.
    - Device class must be allowed for the platform.
    - Unit must be one of the allowed units for that device class.
      If a class lists [None], no unit is allowed.
      Special case: device_class 'monetary' accepts any ISO-4217 3-letter code.
    """

    if device_class not in platform.device_class:
        raise ValueError(
            f"Invalid device_class '{device_class}' for platform '{platform}'. "
            f"Allowed: {platform.device_class}. See {get_entity_spec_help_links(platform)}"
        )

    if unit not in platform.device_class.unit and type(unit) is not MonetaryUnit:
        raise ValueError(
            f"Invalid unit '{unit}' for platform '{platform}' and device_class '{device_class}'. "
            f"Allowed: {platform.device_class.unit}. See {get_entity_spec_help_links(platform)}"
        )

    return platform, device_class, unit
