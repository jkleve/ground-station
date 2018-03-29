from collections import namedtuple
import logging

from .checksum import get_checksum
from .packet_handlers import dispatch_packet

log = logging.getLogger(__name__)

PACKET_HEADER = 0x42
MAX_PACKET_SIZE = 64
MAX_PACKET_DATA_SIZE = MAX_PACKET_SIZE - 1 - 1 - 1  # minus 1 for header, op_code, & data_size


class Packet(object):
    def __init__(self, header, op_code, data_size, data, checksum, raw):
        self.header = header
        self.op_code = op_code
        self.data_size = data_size
        self.data = data
        self.checksum = checksum
        self.raw = raw

    def __iter__(self):
        for d in self.data:
            yield d

    def __repr__(self):
        return 'Packet({self.header}, {self.op_code}, {self.data_size}, {self.data}, {self.checksum}, {self.raw})'\
            .format(**locals())

    def __str__(self):
        opcode = hex(self.op_code)
        return 'Packet(opcode={opcode}, num_data={self.data_size}, data={self.data}, checksum={self.checksum}, ' \
               'raw={self.raw}'.format(**locals())


def generate_packet(op_code, data=None):
    """Take an opcode and data and return an array of bytes to be uplinked
    """
    if data is not None and not isinstance(data, list):
        log.error('generate_packet called and data is not of type list')
        return None

    # the packet's size byte is 1 plus the number of data bytes (1 for opcode byte)
    if data is not None:
        size = len(data) + 1
        p = [PACKET_HEADER, size, op_code] + data
    else:
        size = 1
        p = [PACKET_HEADER, size, op_code]

    p.append(get_checksum(p))

    return p


def packet(data):
    """Take raw data and return a Packet object"""
    header = data[0]
    packet_size = data[1]
    op_code = data[2]
    data_bytes = data[3:-1]
    checksum = data[-1]

    return Packet(header, op_code, packet_size - 1, data_bytes, checksum, data)


def handle_packet(packet):
    """Dispatch packet to the packet handler
    The dispatch destination is determined via the packet's op-code
    """
    computed_checksum = get_checksum(packet.raw[:-1])  # checksum all data but the checksum byte

    # if the checksum is bad lets log and let the packet handler still try to parse it
    if packet.checksum != computed_checksum:
        log.warning('Bad checksum {} {}'.format(computed_checksum, packet))

    log.debug('Dispatching packet {}'.format(packet))
    dispatch_packet(packet)

