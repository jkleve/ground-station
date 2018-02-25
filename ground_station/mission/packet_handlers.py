from logging import getLogger, INFO, DEBUG, WARNING, ERROR
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


def handle_string(packet, level=INFO):
    s = ''.join([chr(b) for b in packet.data])
    log_packet(packet, s, level)


def handle_register(packet):
    value = (packet.data[3] << 8) + packet.data[2]
    register = (packet.data[1] << 8) + packet.data[0]

    try:
        register_name = REGISTERS[register]
    except KeyError:
        register_name = register

    log_packet(packet, 'reg:{} value:{} hex:{}'.format(register_name, value, hex(value)))


def handle_twi_msg(packet):
    try:
        twi_msg = TWI_MESSAGES[packet.data[0]]
    except KeyError:
        twi_msg = packet.data[0]

    log_packet(packet, twi_msg)


def handle_unsigned_data(packet):
    data = [hex(d) for d in packet.data]  # Get the data, excluding the num_bytes
    log_packet(packet, 'unsigned_data: {}'.format(data))


def handle_signed_data(packet):
    # TODO test unsigned, then do this
    data = [hex(d) for d in packet.data]  # Get the data, excluding the num_bytes
    log_packet(packet, 'signed_data: {}'.format(data))


def handle_word(packet):
    word = (packet.data[1] << 8) + packet.data[0]
    log_packet(packet, 'word:{} hex:{}'.format(word, hex(word)))


def handle_byte(packet):
    data = packet.data
    log_packet(packet, 'byte:{} hex:{}'.format(data[0], hex(data[0])))


def handle_size32(packet):
    data = packet.data
    size_32 = (data[3] << 24) + (data[2] << 16) + (data[1] << 8) + data[0]
    log_packet(packet, 'size32:{} hex:{}'.format(size_32, hex(size_32)))


def handle_quaternion(packet):
    handle_string(packet)


def handle_yawpitchroll(packet):
    s = ''.join([chr(b) for b in packet.data])

    # Split into yaw, pitch, & roll
    try:
        yaw, pitch, roll = [float(angle.strip()) for angle in s.split(',')]
    except ValueError:
        log.warning('Invalid yaw, pitch, roll: {}'.format(s))
    else:
        log_packet(packet, 'yaw:{:>7.1f} pitch:{:>7.1f} roll:{:>7.1f}'.format(yaw, pitch, roll))


def handle_user_input(packet):
    s = ''.join([chr(b) for b in packet.data])

    # Split into yaw, pitch, & roll
    yaw, pitch, roll, throttle = [int(value) for value in s.split(',')]
    log_packet(packet, 'yaw:{:>3d} pitch:{:>3d} roll:{:>3d} throttle:{:>3d}'
                    .format(yaw, pitch, roll, throttle))


def handle_downlink_yawpitchroll(packet):
    handle_string(packet, level=INFO)


def handle_change_pid_gain(packet):
    handle_string(packet, level=INFO)


def handle_debug(packet):
    handle_string(packet, level=DEBUG)


def handle_info(packet):
    handle_string(packet, level=INFO)


def handle_warning(packet):
    handle_string(packet, level=WARNING)


def handle_error(packet):
    handle_string(packet, level=ERROR)


def handle_invalid_checksum(packet):
    handle_string(packet, level=WARNING)


def dispatch_packet(packet):
    # if op-code doesn't exists, log a warning
    if packet.op_code not in opcode_to_str:
        log.warning('Invalid op-code \'{}\''.format(packet.op_code))

    else:  # otherwise check if this module has a handler
        handler = 'handle_' + opcode_to_str[packet.op_code]

        log.debug('Dispatching packet to {}'.format(handler))

        # log if this module doesn't have a handler
        if not hasattr(sys.modules[__name__], handler):
            log.warning('No handler for {}'.format(handler))

        else:  # otherwise, dispatch the packet to the handler
            getattr(sys.modules[__name__], handler)(packet)
