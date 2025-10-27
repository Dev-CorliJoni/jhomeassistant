from __future__ import annotations

import re
from typing import List, Tuple


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
    if not isinstance(value, str):
        raise ValueError("discovery_prefix is invalid: value must be a string.")
    if value == "":
        raise ValueError("discovery_prefix is invalid: value must not be empty.")
    if value != value.strip():
        raise ValueError("discovery_prefix is invalid: leading or trailing whitespace is not allowed.")
    if value.startswith("$"):
        raise ValueError("discovery_prefix is invalid: must not start with '$'.")
    if "+" in value or "#" in value:
        raise ValueError("discovery_prefix is invalid: wildcards '+' and '#' are not allowed.")
    if "\x00" in value:
        raise ValueError("discovery_prefix is invalid: null character is not allowed.")
    if any(ch.isspace() for ch in value):
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
    if not isinstance(value, str):
        raise ValueError(f"{id_name} is invalid: value must be a string.")
    if value == "":
        raise ValueError(f"{id_name} is invalid: value must not be empty.")
    if not re.fullmatch(r"^[A-Za-z0-9_-]+$", value):
        raise ValueError(f"{id_name} is invalid: only letters, digits, underscore, and hyphen are allowed.")
    return value


def validate_object_id(value: str) -> str:
    return _validate_discovery_topic_id(value, "object_id")


def validate_node_id(value: str | None) -> str | None:
    return value if value is None else _validate_discovery_topic_id(value, "node_id")


def validate_component(value: str) -> str:
    """
    Validate the component in an MQTT discovery topic (e.g., 'sensor', 'light').

    Rules:
    - Non-empty lowercase with underscores only: ^[a-z_]+$
    - If strict=True, must be in the provided allowlist (SUPPORTED_COMPONENTS by default).
    - No slashes or uppercase characters.
    """
    if not isinstance(value, str):
        raise ValueError("component is invalid: value must be a string.")
    if value == "":
        raise ValueError("component is invalid: value must not be empty.")
    if not re.fullmatch(r"^[a-z_]+$", value):
        raise ValueError("component is invalid: only lowercase letters and underscores are allowed.")

    # Local allowlist exists only during this call; no module-level storage.
    supported = {
        "alarm_control_panel",
        "binary_sensor",
        "button",
        "camera",
        "climate",
        "cover",
        "event",
        "fan",
        "humidifier",
        "light",
        "lock",
        "media_player",
        "number",
        "remote",
        "scene",
        "select",
        "sensor",
        "siren",
        "switch",
        "text",
        "update",
        "vacuum",
        "valve",
        "water_heater",
        "weather",
    }
    if value not in supported:
        raise ValueError(f"component is invalid: '{value}' is not a supported MQTT discovery component.")
    return value


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


def get_allowed_configs():
    return {
        "sensor": {
            None: None,
            "absolute_humidity": ["g/m³", "mg/m³"],
            "apparent_power": ["mVA", "VA", "kVA"],
            "aqi": [None],
            "area": ["m²", "cm²", "km²", "mm²", "in²", "ft²", "yd²", "mi²", "ac", "ha"],
            "atmospheric_pressure": ["cbar", "bar", "hPa", "mmHg", "inHg", "inH₂O", "kPa", "mbar", "Pa", "psi"],
            "battery": ["%"],
            "blood_glucose_concentration": ["mg/dL", "mmol/L"],
            "carbon_dioxide": ["ppm"],
            "carbon_monoxide": ["ppm", "µg/m³", "mg/m³"],
            "conductivity": ["S/cm", "mS/cm", "µS/cm"],
            "current": ["A", "mA"],
            "data_rate": ["bit/s", "kbit/s", "Mbit/s", "Gbit/s", "B/s", "kB/s", "MB/s", "GB/s", "KiB/s", "MiB/s",
                          "GiB/s"],
            "data_size": [
                "bit", "kbit", "Mbit", "Gbit",
                "B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB",
                "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB",
            ],
            "date": [None],
            "distance": ["km", "m", "cm", "mm", "mi", "nmi", "yd", "in"],
            "duration": ["d", "h", "min", "s", "ms", "µs"],
            "energy": ["J", "kJ", "MJ", "GJ", "mWh", "Wh", "kWh", "MWh", "GWh", "TWh", "cal", "kcal", "Mcal", "Gcal"],
            "energy_distance": ["kWh/100km", "Wh/km", "mi/kWh", "km/kWh"],
            "energy_storage": ["J", "kJ", "MJ", "GJ", "mWh", "Wh", "kWh", "MWh", "GWh", "TWh", "cal", "kcal", "Mcal",
                               "Gcal"],
            "enum": [None],
            "frequency": ["Hz", "kHz", "MHz", "GHz"],
            "gas": ["L", "m³", "ft³", "CCF", "MCF"],
            "humidity": ["%"],
            "illuminance": ["lx"],
            "irradiance": ["W/m²", "BTU/(h⋅ft²)"],
            "moisture": ["%"],
            "monetary": ["<ISO 4217 currency code>"],
            "nitrogen_dioxide": ["µg/m³"],
            "nitrogen_monoxide": ["µg/m³"],
            "nitrous_oxide": ["µg/m³"],
            "ozone": ["µg/m³"],
            "ph": [None],
            "pm1": ["µg/m³"],
            "pm25": ["µg/m³"],
            "pm4": ["µg/m³"],
            "pm10": ["µg/m³"],
            "power": ["mW", "W", "kW", "MW", "GW", "TW"],
            "power_factor": ["%", None],
            "precipitation": ["cm", "in", "mm"],
            "precipitation_intensity": ["in/d", "in/h", "mm/d", "mm/h"],
            "pressure": ["cbar", "bar", "hPa", "mmHg", "inHg", "kPa", "mbar", "Pa", "psi", "mPa"],
            "reactive_energy": ["varh", "kvarh"],
            "reactive_power": ["mvar", "var", "kvar"],
            "signal_strength": ["dB", "dBm"],
            "sound_pressure": ["dB", "dBA"],
            "speed": ["ft/s", "in/d", "in/h", "in/s", "km/h", "kn", "m/s", "mph", "mm/d", "mm/s"],
            "sulphur_dioxide": ["µg/m³"],
            "temperature": ["°C", "°F", "K"],
            "temperature_delta": ["°C", "°F", "K"],
            "timestamp": [None],
            "volatile_organic_compounds": ["µg/m³", "mg/m³"],
            "volatile_organic_compounds_parts": ["ppm", "ppb"],
            "voltage": ["V", "mV", "µV", "kV", "MV"],
            "volume": ["L", "mL", "gal", "fl. oz.", "m³", "ft³", "CCF", "MCF"],
            "volume_flow_rate": ["m³/h", "m³/min", "m³/s", "ft³/min", "L/h", "L/min", "L/s", "gal/h", "gal/min",
                                 "mL/s"],
            "volume_storage": ["L", "mL", "gal", "fl. oz.", "m³", "ft³", "CCF", "MCF"],
            "water": ["L", "gal", "m³", "ft³", "CCF", "MCF"],
            "weight": ["kg", "g", "mg", "µg", "oz", "lb", "st"],
            "wind_direction": ["°"],
            "wind_speed": ["ft/s", "km/h", "kn", "m/s", "mph"],
        },

        # NUMBER — mapped from HA doc (differs slightly from sensor, e.g. Beaufort, inH₂O)
        "number": {
            None: [None],
            "absolute_humidity": ["g/m³", "mg/m³"],
            "apparent_power": ["mVA", "VA", "kVA"],
            "aqi": [None],
            "area": ["m²", "cm²", "km²", "mm²", "in²", "ft²", "yd²", "mi²", "ac", "ha"],
            "atmospheric_pressure": ["cbar", "bar", "hPa", "mmHg", "inHg", "inH₂O", "kPa", "mbar", "Pa", "psi"],
            "battery": ["%"],
            "blood_glucose_concentration": ["mg/dL", "mmol/L"],
            "carbon_dioxide": ["ppm"],
            "carbon_monoxide": ["ppm"],
            "current": ["A", "mA"],
            "data_rate": ["bit/s", "kbit/s", "Mbit/s", "Gbit/s", "B/s", "kB/s", "MB/s", "GB/s", "KiB/s", "MiB/s",
                          "GiB/s"],
            "data_size": [
                "bit", "kbit", "Mbit", "Gbit",
                "B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB",
                "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB",
            ],
            "distance": ["km", "m", "cm", "mm", "mi", "nmi", "yd", "in"],
            "duration": ["d", "h", "min", "s", "ms", "µs"],
            "energy": ["J", "kJ", "MJ", "GJ", "mWh", "Wh", "kWh", "MWh", "GWh", "TWh", "cal", "kcal", "Mcal", "Gcal"],
            "energy_distance": ["kWh/100km", "Wh/km", "mi/kWh", "km/kWh"],
            "energy_storage": ["J", "kJ", "MJ", "GJ", "mWh", "Wh", "kWh", "MWh", "GWh", "TWh", "cal", "kcal", "Mcal",
                               "Gcal"],
            "frequency": ["Hz", "kHz", "MHz", "GHz"],
            "gas": ["L", "m³", "ft³", "CCF", "MCF"],
            "humidity": ["%"],
            "illuminance": ["lx"],
            "irradiance": ["W/m²", "BTU/(h⋅ft²)"],
            "moisture": ["%"],
            "monetary": ["<ISO 4217 currency code>"],
            "nitrogen_dioxide": ["µg/m³"],
            "nitrogen_monoxide": ["µg/m³"],
            "nitrous_oxide": ["µg/m³"],
            "ozone": ["µg/m³"],
            "ph": [None],
            "pm1": ["µg/m³"],
            "pm25": ["µg/m³"],
            "pm4": ["µg/m³"],
            "pm10": ["µg/m³"],
            "power_factor": ["%", None],
            "power": ["mW", "W", "kW", "MW", "GW", "TW"],
            "precipitation": ["cm", "in", "mm"],
            "precipitation_intensity": ["in/d", "in/h", "mm/d", "mm/h"],
            "pressure": ["Pa", "kPa", "hPa", "bar", "cbar", "mbar", "mmHg", "inHg", "inH₂O", "psi"],
            "reactive_energy": ["varh", "kvarh"],
            "reactive_power": ["mvar", "var", "kvar"],
            "signal_strength": ["dB", "dBm"],
            "sound_pressure": ["dB", "dBA"],
            "speed": ["ft/s", "in/d", "in/h", "in/s", "km/h", "kn", "m/s", "mph", "mm/d", "mm/s"],
            "sulphur_dioxide": ["µg/m³"],
            "temperature": ["°C", "°F", "K"],
            "volatile_organic_compounds": ["µg/m³", "mg/m³"],
            "volatile_organic_compounds_parts": ["ppm", "ppb"],
            "voltage": ["V", "mV", "µV", "kV", "MV"],
            "volume": ["L", "mL", "gal", "fl. oz.", "m³", "ft³", "CCF", "MCF"],
            "volume_flow_rate": ["m³/h", "m³/min", "m³/s", "ft³/min", "L/h", "L/min", "L/s", "gal/min", "mL/s"],
            "volume_storage": ["L", "mL", "gal", "fl. oz.", "m³", "ft³", "CCF", "MCF"],
            "water": ["L", "gal", "m³", "ft³", "CCF", "MCF"],
            "weight": ["kg", "g", "mg", "µg", "oz", "lb", "st"],
            "wind_direction": ["°"],
            "wind_speed": ["Beaufort", "ft/s", "km/h", "kn", "m/s", "mph"],
        },

        # BINARY SENSOR — units never apply
        "binary_sensor": {
            None: [None],
            "battery": [None],
            "battery_charging": [None],
            "carbon_monoxide": [None],
            "cold": [None],
            "connectivity": [None],
            "door": [None],
            "garage_door": [None],
            "gas": [None],
            "heat": [None],
            "light": [None],
            "lock": [None],
            "moisture": [None],
            "motion": [None],
            "moving": [None],
            "occupancy": [None],
            "opening": [None],
            "plug": [None],
            "power": [None],
            "presence": [None],
            "problem": [None],
            "running": [None],
            "safety": [None],
            "smoke": [None],
            "sound": [None],
            "tamper": [None],
            "update": [None],
            "vibration": [None],
            "window": [None],
        },

        # BUTTON — units never apply
        "button": {
            None: [None],
            "identify": [None],
            "restart": [None],
            "update": [None],
        },

        # COVER — units never apply
        "cover": {
            None: [None],
            "awning": [None],
            "blind": [None],
            "curtain": [None],
            "damper": [None],
            "door": [None],
            "garage": [None],
            "gate": [None],
            "shade": [None],
            "shutter": [None],
            "window": [None],
        },

        # EVENT — units never apply
        "event": {
            None: [None],
            "button": [None],
            "doorbell": [None],
            "motion": [None],
        },

        # HUMIDIFIER — units never apply
        "humidifier": {
            "humidifier": [None],
            "dehumidifier": [None],
        },

        # MEDIA PLAYER — units never apply
        "media_player": {
            "tv": [None],
            "speaker": [None],
            "receiver": [None],
        },

        # SWITCH — units never apply
        "switch": {
            None: [None],
            "outlet": [None],
            "switch": [None],
        },

        # UPDATE — units never apply
        "update": {
            None: [None],
            "firmware": [None],
        },

        # VALVE — units never apply
        "valve": {
            None: [None],
            "water": [None],
            "gas": [None],
        },
    }


def get_entity_spec_help_links(platform: str) -> List[str]:
    return [
                "https://www.home-assistant.io/integrations/homeassistant/#device-class",
                {
                    "binary_sensor": "https://www.home-assistant.io/integrations/binary_sensor/#device-class",
                    "button": "https://www.home-assistant.io/integrations/button/#device-class",
                    "cover": "https://www.home-assistant.io/integrations/cover/#device-class",
                    "event": "https://www.home-assistant.io/integrations/event/#device-class",
                    "humidifier": "https://www.home-assistant.io/integrations/humidifier/#device-class",
                    "media_player": "https://www.home-assistant.io/integrations/media_player/#device-class",
                    "number": "https://www.home-assistant.io/integrations/number/#device-class",
                    "sensor": "https://www.home-assistant.io/integrations/sensor#device-class",
                    "switch": "https://www.home-assistant.io/integrations/switch/#device-class",
                    "update": "https://www.home-assistant.io/integrations/update/#device-class",
                    "valve": "https://www.home-assistant.io/integrations/valve/#device-class"
                }[platform]
            ]


def validate_entity_spec(
    platform: str,
    device_class: str | None,
    unit_of_measurement: str | None,
) -> Tuple[str, str | None, str | None]:
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
    allowed_config = get_allowed_configs()

    if platform not in allowed_config:
        allowed_platforms = sorted(allowed_config.keys())
        raise ValueError(
            f"Unsupported platform '{platform}'. Allowed: {allowed_platforms}. See {get_entity_spec_help_links('sensor')}"
        )

    allowed_device_class_map = allowed_config[platform]
    if device_class not in allowed_device_class_map:
        allowed_dcs = sorted([str(k) for k in allowed_device_class_map.keys()])
        raise ValueError(
            f"Invalid device_class '{device_class}' for platform '{platform}'. "
            f"Allowed: {allowed_dcs}. See {get_entity_spec_help_links(platform)}"
        )

    allowed_units = allowed_device_class_map[device_class]
    # If allowed_units contains the literal "<ISO 4217 currency code>", accept any ISO-4217 code too (sensor mapping).
    if "<ISO 4217 currency code>" in allowed_units:
        if unit_of_measurement is None or not re.match(r"^[A-Z]{3}$", unit_of_measurement):
            raise ValueError(
                f"Invalid unit '{unit_of_measurement}' for {platform} with device_class 'monetary'. "
                f"Allowed: 3-letter ISO 4217 currency code. See {get_entity_spec_help_links(platform)}"
            )
    elif unit_of_measurement not in allowed_units:
        raise ValueError(
            f"Invalid unit_of_measurement '{unit_of_measurement}' for platform '{platform}' and device_class '{device_class}'. "
            f"Allowed: {allowed_units}. See {get_entity_spec_help_links(platform)}"
        )

    return platform, device_class, unit_of_measurement
