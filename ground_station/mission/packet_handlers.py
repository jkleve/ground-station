from logging import getLogger, INFO
import sys

from .opcodes import opcode_to_str

log = getLogger(__name__)

REGISTERS = dict([
    (0x90, 'TCCR3A'),
    (0x91, 'TCCR3B'),
    (0x92, 'TCCR3C'),
    (0x94, 'TCNT3'),
    (0x96, 'ICR3'),
    (0x98, 'OCR3A'),
    (0x9A, 'OCR3B'),
    (0x9C, 'OCR3C'),
    (0xB8, 'TWBR'),
    (0xB9, 'TWSR'),
    (0xBC, 'TWCR'),
    (0x124, 'TCNT5')
])

TWI_MESSAGES = dict([
    (0x08, 'Start sent'),
    (0x10, 'Repeated start sent'),
    (0x18, 'SLA+W transmitted, received ACK'),
    (0x20, 'SLA+W transmitted, received NACK'),
    (0x28, 'Data transmitted, received ACK'),
    (0x30, 'Data transmitted, received NACK'),
    (0x38, 'Arbitration lost in SLA+W or data bytes'),
    (0x40, 'SLA+R transmitted, received ACK'),
    (0x48, 'SLA+R transmitted, received NACK'),
    (0x50, 'Data received, transmitted ACK'),
    (0x58, 'Data received, transmitted NACK')
])


def log_packet(packet, message, level=INFO):
    log.log(level, '({:16}): {}'.format(opcode_to_str[packet.op_code], message))


def handle_string(packet):
    s = ''.join([chr(b) for b in packet.data])
    log_packet(packet, s)


def handle_register(packet):
    value = (packet.data[3] << 8) + packet.data[2]
    register = (packet.data[1] << 8) + packet.data[0]

    try:
        register_name = REGISTERS[register]
    except KeyError:
        register_name = register

    log_packet(packet, 'reg:{} value:{} hex:{}'.format(register_name, value, hex(value)))


def dispatch_packet(packet):
    # if op-code doesn't exists, log a warning
    if packet.op_code not in opcode_to_str:
        log.warning('Invalid op-code \'{}\''.format(packet.op_code))

    else:  # otherwise check if this module has a handler
        handler = 'handle_' + opcode_to_str[packet.op_code]

        # log if this module doesn't have a handler
        if not hasattr(sys.modules[__name__], handler):
            log.warning('No handler for {}'.format(handler))

        else:  # otherwise, dispatch the packet to the handler
            getattr(sys.modules[__name__], handler)(packet)
