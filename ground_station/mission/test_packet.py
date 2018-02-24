import logging

from packet import *
from opcodes import opcode_to_hex


log = logging.getLogger(__file__)


def test_handle_string():
    string = 'hello'
    length = 1 + len(string) + 1  # length includes op_code, data, and crc
    op_code = opcode_to_hex['string']

    packet = [PACKET_HEADER, length, op_code, 'h', 'e', 'l', 'l', 'o']

    checksum = get_checksum(packet)

    packet.append(checksum)

    handle_packet(packet)


if __name__ == '__main__':
    test_handle_string()
