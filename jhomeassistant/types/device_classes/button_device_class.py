from jhomeassistant.types.device_classes.base_device_class import BaseDeviceClass


class ButtonDeviceClass(BaseDeviceClass):
    NONE = None
    IDENTIFY = "identify"
    RESTART = "restart"
    UPDATE = "update"
