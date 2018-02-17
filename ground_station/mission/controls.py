from ctypes import c_uint8
from multiprocessing import Array

from .opcodes import opcode_to_hex
from .packet import generate_packet


class Controls(object):
    def __init__(self):
        self.values = Array(c_uint8, (50, 50, 50, 0))

    @property
    def yaw(self):
        return self.values[0]

    @yaw.setter
    def yaw(self, yaw):
        self.values[0] = yaw

    @property
    def pitch(self):
        return self.values[1]

    @pitch.setter
    def pitch(self, pitch):
        self.values[1] = pitch

    @property
    def roll(self):
        return self.values[2]

    @roll.setter
    def roll(self, roll):
        self.values[2] = roll

    @property
    def throttle(self):
        return self.values[3]

    @throttle.setter
    def throttle(self, throttle):
        self.values[3] = throttle

    def get_state(self):
        return self.yaw, self.pitch, self.roll, self.throttle

    def get(self, block=False):
        """Implement get to be like a FIFO queue which is what UplinkService requires.
        It does not need to throw a queue.Empty exception as long as it always returns something"""
        op_code = opcode_to_hex['controls']
        controls = [self.yaw, self.pitch, self.roll, self.throttle]
        return generate_packet(op_code, controls)
