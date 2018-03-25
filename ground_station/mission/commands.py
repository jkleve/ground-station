from logging import getLogger
from queue import Queue
import signal
import sys

from mission.controls import Controls
from mission.events import CommandEvent, EVENT_TYPE
from mission.opcodes import opcode_to_hex
from mission.packet import generate_packet
from mission.user_input import UserInput
from service import Service, ServiceManager


class Commanding(object):
    def __init__(self, send_handler, frequency):
        self.log = getLogger(self.__class__.__name__)
        self.send = send_handler
        # Controls shared object
        self.controls = Controls()
        # Commands uplink queue
        self.commands = Queue()

        # Uplink services uplink generated packets at certain frequency
        self.uplink_services = ServiceManager([
            Service('Controls', self.send, self.controls, frequency, 1),
            Service('Commands', self.command_handler, self.commands, frequency, 2),
        ])

        self.user_input = UserInput(self.controls, self.commands)
        self.user_input.non_flight()

        def signal_handler(sig_num, frame):
            self.log.info('Shutting down')
            self.uplink_services.stop('Controls')
            self.uplink_services.stop('Commands')
            self.user_input.stop(True)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        self.uplink_services.start('Commands')

        self.user_input.run()

    def command_handler(self, event):
        if event[EVENT_TYPE] == CommandEvent.ENTER_FLIGHT_MODE:
            self.enter_flight_mode()
            self.send(generate_packet(opcode_to_hex['flight_mode']))
        elif event[EVENT_TYPE] == CommandEvent.EXIT_FLIGHT_MODE:
            self.exit_flight_mode()
            self.send(generate_packet(opcode_to_hex['non_flight_mode']))
        elif event[EVENT_TYPE] == CommandEvent.TOGGLE_YAWPITCHROLL:
            self.send(generate_packet(opcode_to_hex['downlink_yawpitchroll']))

    def enter_flight_mode(self):
        self.log.info('Entering flight mode')

        self.user_input.flight()
        self.uplink_services.start('Controls')

    def exit_flight_mode(self):
        self.log.info('Exiting flight mode')

        self.uplink_services.stop('Controls')
        self.user_input.non_flight()
