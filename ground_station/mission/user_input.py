from logging import getLogger
from map_input import Input, un_intialize, initialize
from .events import ControlEvent, CommandEvent, EVENT_TYPE, EVENT_VALUE
from .user_mappings import flight_controls, non_flight_controls


class UserInput(object):
    def __init__(self, controls_obj, command_event_q):
        from queue import Queue
        from threading import Thread, Event

        self.log = getLogger(self.__class__.__name__)

        initialize(joystick=True)  # initialize map_input

        self.stop_flag = Event()
        self._event_queue = Queue()

        self._input = Input(self._event_queue, self.stop_flag.is_set, non_flight_controls)

        self._input_thread = Thread(name='User Input', target=self._input.run)
        self._input_thread.start()

        self._controls = controls_obj
        self._commands = command_event_q

    def flight(self):
        self._input.mapping = flight_controls

    def non_flight(self):
        self._input.mapping = non_flight_controls

    def stop(self, kill_all=False):
        if kill_all:
            un_intialize()

        if self._input is not None:
            self.stop_flag.set()
            self._input_thread.join()

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
        self._commands.put(event)  # forward event to command_handler via Command service

    def run(self):
        while True:
            event = self._event_queue.get()
            self.log.debug('Event: {}'.format(event))

            if isinstance(event[EVENT_TYPE], ControlEvent):
                self.control_event(event)
            elif isinstance(event[EVENT_TYPE], CommandEvent):
                self.command_event(event)
            else:
                self.log.warning('Unknown event {}'.format(event))

