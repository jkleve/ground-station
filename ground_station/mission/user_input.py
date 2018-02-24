from logging import getLogger
from map_input import InputThread, un_intialize
from .events import ControlEvent, CommandEvent, EVENT_TYPE, EVENT_VALUE
from .opcodes import opcode_to_hex, is_command, is_controls
from .packet import generate_packet
from .user_mappings import flight_controls, non_flight_controls


class UserInput(object):
    def __init__(self, controls_obj, command_event_q):
        from queue import Queue

        self.log = getLogger(str(self.__class__))
        self._input = None
        self._event_queue = Queue()

        self._controls = controls_obj
        self._commands = command_event_q

    def flight(self):
        self.stop()

        self._input = InputThread(self._event_queue, flight_controls)
        self._input.start()

    def non_flight(self):
        self.stop()

        self._input = InputThread(self._event_queue, non_flight_controls)
        self._input.start()

    def stop(self, kill_all=False):
        if kill_all:
            un_intialize()

        if self._input is not None:
            self._input.stop()

    def control_event(self, event):
        if event[EVENT_TYPE] == ControlEvent.YAW:
            self._controls.yaw = event[EVENT_VALUE]
        elif event[EVENT_TYPE] == ControlEvent.PITCH:
            self._controls.pitch = event[EVENT_VALUE]
        elif event[EVENT_TYPE] == ControlEvent.ROLL:
            self._controls.roll = event[EVENT_VALUE]
        elif event[EVENT_TYPE] == ControlEvent.THROTTLE:
            self._controls.throttle = event[EVENT_VALUE]

    def command_event(self, event):
        p = None

        if event[EVENT_TYPE] == CommandEvent.ENTER_FLIGHT_MODE:
            self.flight()
            p = generate_packet(opcode_to_hex['flight_mode'])
        elif event[EVENT_TYPE] == CommandEvent.EXIT_FLIGHT_MODE:
            self.non_flight()
            p = generate_packet(opcode_to_hex['non_flight_mode'])

        if p is None:  # should never happen as long as run() is handling this error
            self.log.warning('user_input.command_event was called with an invalid event type!')
            return

        self.log.info(p)
        self._commands.put(p)

    def run(self):
        while True:
            event = self._event_queue.get()
            print(event)

            if isinstance(event[EVENT_TYPE], ControlEvent):
                self.control_event(event)
            elif isinstance(event[EVENT_TYPE], CommandEvent):
                self.command_event(event)
            else:
                self.log.warning('Unknown event {}'.format(event))

