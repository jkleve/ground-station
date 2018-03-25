from logging import getLogger
from mission import *
import struct


class Receiver(object):
    def __init__(self, connection, stop):
        """Receiver thread class"""
        self._connection = connection
        self._stop = stop

        self.log = getLogger(self.__class__.__name__)

    @property
    def connection(self):
        return self._connection

    def run(self):
        """Run the receiver thread
        This method assumes a specific packet layout with 1 byte fields

        Packet layer:
        [HEADER] [SIZE] [OP-CODE] [DATA] ... [CHECKSUM]

        """
        self.log.info("Starting")

        while not self._stop():
            byte = self.get_byte()

            if byte is None:
                continue
            elif byte == PACKET_HEADER:
                size = self.get_byte()

                if size is None:
                    self.log.warning('Got \'None\' when trying to get packet size')
                    continue

                # discard packets that are too big
                if size > MAX_PACKET_DATA_SIZE:
                    self.log.warning('Packet \'size\' field indicates MAX_PACKET_DATA_SIZE exceeded ({} > {})'
                                     .format(size, MAX_PACKET_DATA_SIZE))
                    continue

                data = list()

                for _ in range(0, size + 1):  # plus 1 for checksum byte
                    data.append(self.get_byte())

                p = packet([byte, size] + data)
                self.log.debug('Received packet {}'.format(p))
                handle_packet(p)

            else:  # byte != self.header
                self.log.warning('Received non-header byte \'{}\''.format(byte))

    def quit(self):
        pass  # Maybe return a code?

    def scan_for(self, byte):
        pass

    def get_byte(self):
        """Get one byte from connection

        This method handles all data as an unsigned byte
        """
        try:
            b = self.connection.read(1)
        except IOError:
            self.log.critical("")  # Add some extra emphasis
            self.log.critical("Device disconnected. Exiting ...")
            return None

        if len(b) > 0:
            b = struct.unpack('B', b)[0]
            return b


