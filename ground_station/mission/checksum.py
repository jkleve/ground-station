def get_checksum(data):
    checksum = 0

    for d in data:
        checksum += d

    checksum = checksum % 0x100

    # Get inverse and convert to unsigned
    return ~checksum + 2**8


