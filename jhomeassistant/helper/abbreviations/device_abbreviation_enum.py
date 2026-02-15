from enum import Enum


class DeviceAbbreviation(Enum):
    NAME = ("name", "name")
    IDS = ("identifiers", "ids")
    CONNECTIONS = ("connections", "cns")
    SERIAL_NUMBER = ("serial_number", "sn")
    MANUFACTURER = ("manufacturer", "mf")
    MODEL = ("model", "mdl")
    MODEL_ID = ("model_id", "mdl_id")
    HW = ("hw_version", "hw")
    SW = ("sw_version", "sw")
    VIA_DEVICE = ("via_device", "via_device")
    URL = ("configuration_url", "cu")
    SUGGESTED_AREA = ("suggested_area", "sa")
