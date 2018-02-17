from logging import getLogger
from map_input import event_queue, InputProcess
from .events import ControlEvent, CommandEvent, EVENT_TYPE, EVENT_VALUE
from .packet import generate_packet
from .user_mappings import flight_controls, non_flight_controls


class UserInputProcess(object):
    def __init__(self, controls_obj, command_event_q):
        self.log = getLogger(str(self.__class__))
        self._input = None
        self._controls = controls_obj
        self._commands = command_event_q

    def flight(self):
        self.stop()

        self._input = InputProcess(flight_controls)
        self._input.start()

    def non_flight(self):
        self.stop()

        self._input = InputProcess(non_flight_controls)
        self._input.start()

    def stop(self):
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
        # TODO how do we want to go to flight mode mappings? Send the command to the quad, hope it sticks,
        # and switch ourselves to flight mode? Probably the easiest for first release
        p = generate_packet(0, event[EVENT_VALUE])
        self._commands.put(p)
        # TODO map CommandEvents to data that can be used to call packet.generate_packet(op_code, data)

    def run(self):
        while True:
            event = event_queue.get()

            if isinstance(event, ControlEvent):
                self.control_event(event)
            elif isinstance(event, CommandEvent):
                self.command_event(event)
            else:
                self.log.warning('Unknown event {}'.format(event))

