UNUSED = 'unused'

opcode_to_str = {
    # telemetry
    0x00: 'string',
    0x01: 'twi_msg',
    0x02: 'register',
    0x03: 'unsigned_data',
    0x04: 'signed_data',
    0x05: 'quaternion',
    0x06: 'yawpitchroll',
    0x07: 'byte',
    0x08: 'word',
    0x09: 'size32',
    0x0a: 'motor_values',
    0x0b: 'pid_outputs',
    0x0c: 'user_input',  # TODO remove things like this. move towards logging functions
    0x0d: UNUSED,
    0x0e: UNUSED,
    0x0f: UNUSED,

    # commands
    0x20: 'controls',
    0x21: 'change_pid_gain',
    0x22: 'downlink_yawpitchroll',
    0x23: 'flight_mode',
    0x24: UNUSED,
    0x25: 'terminate',


    # errors
    0x30: 'not_header',
    0x31: 'invalid_packet',
    0x32: 'invalid_checksum',
    0x33: 'downlink_buffer_overrun',

    # logs
    0x40: 'debug',
    0x41: 'info',
    0x42: 'warning',
    0x43: 'error',
}

opcode_to_hex = {v: k for k, v in opcode_to_str.items()}


def get_opcode(op_code):
    if isinstance(op_code, str):
        return opcode_to_hex[op_code]
    elif isinstance(op_code, hex):
        return opcode_to_str[op_code]

    return 'invalid'  # User gave bad input


