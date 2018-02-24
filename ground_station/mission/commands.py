from logging import getLogger
from multiprocessing import Event, Process, Queue
import signal
import sys

from mission.controls import Controls
from mission.events import CommandEvent
from mission.user_input import UserInput
from service import Service, ServiceManager


class Commanding(object):
    def __init__(self, transmitter, frequency):
        self.log = getLogger(str(self.__class__))
        # Controls shared object
        self.controls = Controls()
        # Commands uplink queue
        self.commands = Queue()

        # Uplink services
        self.uplink_services = ServiceManager([
            Service('Controls', transmitter.send, self.controls, frequency, 1),
            Service('Commands', self.command_handler, self.commands, frequency, 2),
        ])

        self.user_input = UserInput(self.controls, self.commands)
        self.user_input.non_flight()

        def signal_handler(sig_num, frame):
            self.log.info('Shutting down')
            self.user_input.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        self.user_input.run()

        self.uplink_services.start('Commands')

    def command_handler(self, command):
        if command == CommandEvent.ENTER_FLIGHT_MODE:
            self.enter_flight_mode()
        if command == CommandEvent.EXIT_FLIGHT_MODE:
            self.exit_flight_mode()

    def enter_flight_mode(self):
        print('entering flight mode')
        self.user_input.flight()

        self.uplink_services.start('Controls')

    def exit_flight_mode(self):
        print('exiting flight mode')
        self.uplink_services.stop('Controls')

        self.user_input.non_flight()
