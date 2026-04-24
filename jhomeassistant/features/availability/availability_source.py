from enum import StrEnum


class AvailabilitySource(StrEnum):
    CONNECTION = "connection"
    ORIGIN = "origin"
    DEVICE = "device"
    ENTITY = "entity"
