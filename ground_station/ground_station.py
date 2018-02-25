from argparse import ArgumentParser
from errno import EACCES, EPERM
import logging
from logging import DEBUG, INFO, WARNING, ERROR
from multiprocessing import Event, Process
from pathlib import Path
import serial
import signal
import sys
import time

from receiver import Receiver
from transmit import Transmitter

from mission.commands import Commanding


def config_log(log_name, log_filename=None, file_fmt='%(asctime)8s %(levelname)7s: %(message)s',
               file_datefmt='%H:%M:%S', file_level=logging.DEBUG, log_stream=None,
               stream_fmt='%(asctime)8s %(levelname)7s: %(message)s', stream_datefmt='%H:%M:%S',
               stream_level=logging.INFO):

    # Get log and set level to lowest level
    log = logging.getLogger(log_name)
    log.propagate = False  # don't propagate to root logger. not sure this is what we want but stops duplicate prints
    log.setLevel(logging.DEBUG)

    # Create file handler & add it to log
    if log_filename:
        if not Path(log_filename).parent.exists():
            Path(log_filename).parent.mkdir()

        file_format = logging.Formatter(fmt=file_fmt, datefmt=file_datefmt)
        file_log_handler = logging.FileHandler(log_filename)

        file_log_handler.setFormatter(file_format)
        file_log_handler.setLevel(file_level)
        # Add handle to the log
        log.addHandler(file_log_handler)

    # Create stream handler & add it to log
    if log_stream:
        stream_format = logging.Formatter(fmt=stream_fmt, datefmt=stream_datefmt)
        stream_log_handler = logging.StreamHandler(stream=log_stream)

        stream_log_handler.setFormatter(stream_format)
        stream_log_handler.setLevel(stream_level)
        # Add handle to the log
        log.addHandler(stream_log_handler)

    return log


def config_logs(logs):
    max_name_length = 0
    log_ms = False

    for log in logs:
        name = log['log_name']
        if len(name) > max_name_length:
            max_name_length = len(name)

        if log['log_ms']:
            log_ms = True

        ms = '.%(msecs)3d' if log_ms else ''

        file_fmt = '%(asctime)8s{ms} %(name){name_length}s: %(levelname)7s: %(message)s'.format(ms=ms,
                                                                                                name_length=
                                                                                                max_name_length)

        stream_fmt = '%(asctime)8s{ms}: %(name){name_length}s %(levelname)7s: %(message)s'.format(ms=ms,
                                                                            name_length=max_name_length)
        datefmt = '%H:%M:%S'

        log.pop('log_ms', None)  # remove log_ms from log dict because config_log doesn't take a log_ms kwarg

        config_log(**log, file_fmt=file_fmt, file_datefmt=datefmt, stream_fmt=stream_fmt, stream_datefmt=datefmt)


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
                errno = e.errno if hasattr(e, 'errno') else None
                # Check if the exception was due to permissions
                if errno == EPERM or errno == EACCES:
                    logging.error("Permissions denied to create serial connection")
                    sys.exit(EPERM)
            else:
                logging.info("Connected on {}".format(port))
                break

    return connection


# class MockConnection(object):
#     def __init__(self):
#         pass
#
#     def write(self, data):
#         print('MockConnection: {}'.format(data))
#
#     def read(self, num_bytes):
#         time.sleep(1)  # delay to slow the receiver process down
#         return b'b'


# def connect():
#     return MockConnection()


def main():
    parser = ArgumentParser(description="Ground station for quadcopter flight code")
    parser.add_argument('-ms', action='store_true', help="Print time with milli-seconds")
    parser.add_argument('-t', '--controls-transmit-frequency', type=int, default=5,
                        help="User input uplink frequency (Hz)")

    args = parser.parse_args()

    logs = ({
                'log_name': 'Receiver',
                'log_filename': 'logs/receiver.log',
                # 'log_stream': sys.stdout,
                'log_ms': args.ms,
                'stream_level': DEBUG,
                'file_level': DEBUG,
            },
            {
                'log_name': 'mission.packet_handlers',
                'log_filename': 'logs/packet_handler.log',
                'log_stream': sys.stdout,
                'stream_level': INFO,
                'log_ms': args.ms,
            },
            {
                'log_name': 'mission.packet',
                'log_filename': 'logs/packet.log',
                'log_stream': sys.stdout,
                'stream_level': INFO,
                'log_ms': args.ms,
            },
            {
                'log_name': 'Transmitter',
                'log_filename': 'logs/transmitter.log',
                'log_ms': args.ms,
            },
            {
                'log_name': 'Commanding',
                'log_filename': 'logs/commanding.log',
                'file_level': DEBUG,
                'stream_level': DEBUG,
                'log_ms': args.ms,
            },
            {
                'log_name': 'UserInput',
                'log_filename': 'logs/user_input.log',
                'file_level': DEBUG,
                'stream_level': DEBUG,
                'log_ms': args.ms,
            },
            {
                'log_name': 'ServiceManager',
                'log_filename': 'logs/services.log',
                'log_stream': sys.stdout,
                'file_level': DEBUG,
                'stream_level': INFO,
                'log_ms': args.ms,
            })

    # other logs:
    # CommandService
    # ControlsService

    config_logs(logs)

    connection = connect()
    connection.timeout = 0.1

    # stop event to stop receiver
    stop_flag = Event()

    # receiver
    receive = Receiver(connection, stop_flag.is_set)
    receiver = Process(target=receive.run)

    # transmitter
    transmitter = Transmitter(connection)

    # user input & commanding
    commanding = Process(target=Commanding, args=(transmitter, 20))  # command at 20 Hz

    # signal_handler to gracefully exit
    def signal_handler(sig_num, frame):
        stop_flag.set()

        try:
            commanding.terminate()  # commanding process should receive sigint too
            receiver.terminate()
            commanding.join(10)
            receiver.join(10)
        except AttributeError:
            pass  # ignore this. commanding exited on its own

        sys.exit(0)

    # register SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    # start receiver
    receiver.start()
    # start user input & command handling
    commanding.start()

    while True:
        pass


if __name__ == '__main__':
    main()

    sys.exit(0)
