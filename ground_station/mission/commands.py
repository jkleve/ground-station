from logging import getLogger
from multiprocessing import Queue
import signal
import sys
from threading import Thread

from mission.controls import Controls
from mission.events import CommandEvent
from mission.user_input import UserInput
from service import Service, ServiceManager


class Commanding(object):
    def __init__(self, transmitter, frequency):
        self.log = getLogger(self.__class__.__name__)
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

        self.command_thread = Thread(target=self.uplink_services.start, args=('Commands',))
        self.command_thread.start()
        self.controls_thread = None
        # self.uplink_services.start('Commands')

        self.user_input.run()

    def command_handler(self, command):
        if command == CommandEvent.ENTER_FLIGHT_MODE:
            self.enter_flight_mode()
        if command == CommandEvent.EXIT_FLIGHT_MODE:
            self.exit_flight_mode()

    def enter_flight_mode(self):
        self.log.info('Entering flight mode')
        self.user_input.flight()

        self.controls_thread = Thread(target=self.uplink_services.start, args=('Controls',))
        # self.uplink_services.start('Controls')

    def exit_flight_mode(self):
        self.log.info('Exiting flight mode')
        # self.uplink_services.stop('Controls')
        self.controls_thread.terminate()
        self.controls_thread.join(1)
        self.controls_thread = None

        self.user_input.non_flight()
