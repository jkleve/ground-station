from argparse import ArgumentParser
from errno import EACCES, EPERM
import logging
from logging import DEBUG, INFO, WARNING, ERROR
import multiprocessing
from multiprocessing import Process
import serial
import signal
import sys
import time

#from .transmit import Transmitter


def config_log(log_name, log_filename=None, log_stream=None, log_ms=False,
            stream_level=logging.INFO, file_level=logging.DEBUG):
    # Logger
    log = logging.getLogger(log_name)
    log.setLevel(logging.DEBUG)
    log.propagate = False  # TODO this is to stop double logging. It seems there is a default handler going to stdout

    # File handler
    if log_filename:
        if log_ms:
            file_format = logging.Formatter(fmt='%(asctime)8s.%(msecs).3d %(levelname)7s: %(message)s',
                                            datefmt='%m/%d %H:%M:%S')
        else:
            file_format = logging.Formatter(fmt='%(asctime)8s%(name)16s: %(levelname)7s: %(message)s',
                                            datefmt='%m/%d %H:%M:%S')
        file_log_handler = logging.FileHandler(log_filename)
        file_log_handler.setFormatter(file_format)
        file_log_handler.setLevel(file_level)
        # Add handle to the log
        log.addHandler(file_log_handler)

    # Stream handler
    if log_stream:
        if log_ms:
            stream_format = logging.Formatter(fmt='%(asctime)8s.%(msecs)3d %(levelname)7s: %(message)s',
                                              datefmt='%H:%M:%S')
            #stream_format = logging.Formatter(fmt='%(asctime)8s%(name)16s: %(levelname)7s: %(message)s',
            #                                  datefmt='%H:%M:%S')
        else:
            stream_format = logging.Formatter(fmt='%(asctime)8s%(name)16s: %(levelname)7s: %(message)s',
                                              datefmt='%H:%M:%S')
        stream_log_handler = logging.StreamHandler(stream=log_stream)
        stream_log_handler.setFormatter(stream_format)
        stream_log_handler.setLevel(stream_level)
        # Add handle to the log
        log.addHandler(stream_log_handler)

    return log


def connect():
    timeout = 0  # Seconds
    start_time = time.time()
    ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyUSB0']
    connection = None

    logging.info("Attempting to connect to device")
    while connection is None:
        if 0 < timeout < time.time() - start_time:
            logging.error("Timed out connecting to device")
            break

        for port in ports:
            try:
                connection = serial.Serial(port=port,
                                           baudrate=38400,
                                           bytesize=serial.EIGHTBITS,
                                           parity=serial.PARITY_NONE,
                                           stopbits=serial.STOPBITS_ONE,
                                           timeout=2)  # This timeout is for if the port actually exists
            except Exception as e:
                # Check if the exception was due to sudo permissions
                if e.errno == EPERM or e.errno == EACCES:
                    logging.error("Need sudo permissions")
                    sys.exit(1)
            else:
                logging.info("Connected on {}".format(port))
                break

    return connection


def new_main():
    connection = connect()
    connection.timeout = 0.1

    from multiprocessing import Event, Process, Queue

    from mission.controls import Controls
    from .receiver import Receiver
    from .transmit import Transmitter
    from .service import Service, ServiceManager

    stop_flag = Event()

    # receiver
    receive = Receiver(connection, stop_flag)
    receiver = Process(target=receive.run)

    # transmitter
    transmitter = Transmitter(connection)

    # Controls shared object
    controls = Controls()
    # Commands uplink queue
    commands = Queue()
    uplink_frequency = 20

    # Uplink services
    uplink_services = ServiceManager([
        Service('Controls', transmitter.send, controls, uplink_frequency),
        Service('Commands', transmitter.send, commands, uplink_frequency),
    ])
    uplink_services.start('Commands')

    # start receiver
    receiver.start()


def main():
    from mission.packet_handlers import dispatch_packet
    from mission.packet import packet
    dispatch_packet(packet([0, 0, 0x00, 1, 2, 3, 0]))
    sys.exit()

    parser = ArgumentParser(description="Ground station for quadcopter flight code")
    parser.add_argument('-ms', action='store_true', help="Print time with milli-seconds")
    parser.add_argument('-t', '--controls-transmit-frequency', type=int, default=5,
                        help="User input uplink frequency (Hz)")

    args = parser.parse_args()

    user_transmit_frequency = args.controls_transmit_frequency

    # Connection to hardware
    connection = connect()
    connection.timeout = 0.1

    logs = ({
                'log_name': 'Receiver',
                'log_filename': 'logs/receiver_log.log',
                'log_stream': sys.stdout,
                'log_ms': args.ms,
                'stream_level': WARNING,
                'file_level': DEBUG,
            },
            {
                'log_name': 'PacketHandler',
                'log_filename': 'logs/packet_log.log',
                'log_stream': sys.stdout,
                'log_ms': args.ms,
            },
            {
                'log_name': 'Transmitter',
                'log_filename': 'logs/transmitter_log.log',
                'log_ms': args.ms,
            },
            {
                'log_name': 'UplinkControls',
                'log_filename': 'logs/uplink_controls_log.log',
                'file_level': INFO,
                'log_ms': args.ms,
            })

    receiver_log, \
    packet_log, \
    transmitter_log, \
    uplink_controls_log \
        = [config_log(**log) for log in logs]

    # Receiver (downlink)
    packet_handler_obj = PacketHandler(logger=packet_log)

    receiver = Receiver(connection=connection, stop_flag=stop_flag_process,
                        packet_handler=packet_handler_obj.handle_packet,
                        compute_checksum=get_checksum)
    receiver_process = Process(target=receiver.run)
    receiver_process.start()

    # User input

    # Transmitter
    transmitter = Transmitter(connection)

    # TODO Send commands, listen, command to flight, then continue to controls_uplink_process

    # Commanding (uplink) runs at a certain frequency
    controls_uplink = UplinkControls(transmitter=transmitter, frequency=user_transmit_frequency,
                                     stop_flag=stop_flag_process, logger=uplink_controls_log)
    controls_uplink_process = Process(target=controls_uplink.run)
    controls_uplink_process.start()

    # TODO add more logic on the ground station side to automate the initialization and maybe have a menu on config vs start flight
    # TODO start this when we are going into flight mode

    receiver_process.join()
    user_input_process.join()
    controls_uplink_process.join()


if __name__ == '__main__':
    # Run main function until we exit or catch an exception
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.info('Caught SIGINT. Exiting ground_station')
        sys.exit(0)

    sys.exit(0)
