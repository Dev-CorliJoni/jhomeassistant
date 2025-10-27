from enum import StrEnum


class EntityCategory(StrEnum):
    """
    Entity categories supported by Home Assistant.

    - CONFIG: Entity configures a device (shows under "Settings"/"Configuration").
    - DIAGNOSTIC: Entity provides diagnostics/telemetry for a device.
    """
    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"
