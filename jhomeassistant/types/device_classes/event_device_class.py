from jhomeassistant.types.device_classes.base_device_class import BaseDeviceClass


class EventDeviceClass(BaseDeviceClass):
    NONE = None
    BUTTON = "button"
    DOORBELL = "doorbell"
    MOTION = "motion"
