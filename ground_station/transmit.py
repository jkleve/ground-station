from logging import getLogger
import struct
import time


class Transmitter(object):
    def __init__(self, connection):
        # Initialize logger
        self.log = getLogger(self.__class__.__name__)

        # Save connection
        self.connection = connection

    def send(self, packet):
        for byte in packet:
            if self.connection is not None:
                self.log.info('Sending {}'.format(packet))
                self.connection.write(struct.pack('B', byte))
                time.sleep(0.01)  # Delay so apm has time to receive byte


