from enum import Enum

EVENT_TYPE = 0
EVENT_VALUE = 1


class ControlEvent(Enum):
    YAW = 0
    PITCH = 1
    ROLL = 2
    THROTTLE = 3


class CommandEvent(Enum):
    Test = 1

