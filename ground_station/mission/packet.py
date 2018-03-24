from collections import namedtuple
import logging

from .checksum import get_checksum
from .packet_handlers import dispatch_packet

log = logging.getLogger(__name__)

Packet = namedtuple('Packet', ['header', 'op_code', 'data_size', 'data', 'checksum', 'raw'])

PACKET_HEADER = 0x42
MAX_PACKET_SIZE = 64
MAX_PACKET_DATA_SIZE = MAX_PACKET_SIZE - 1 - 1 - 1  # minus 1 for header, op_code, & data_size


def generate_packet(op_code, data=None):
    """Take an opcode and data and return an array of bytes to be uplinked
    """
    if data is not None and not isinstance(data, list):
        log.error('generate_packet called and data is not of type list')
        return None

    # the packet's size byte is 2 plus the number of data bytes (1 for header byte and 1 for opcode byte)
    if data is not None:
        size = 1 + len(data) + 1
        p = [PACKET_HEADER, size, op_code] + data
    else:
        size = 2
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

