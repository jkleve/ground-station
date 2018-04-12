from errno import EPERM, EACCES
import logging
import logging.config
from pathlib import Path
import serial
import sys
import time

LOGGING_FORMAT = '%(asctime)s %(levelname)-8s %(name)s: %(message)s'
LOGGING_DATEFMT = '%H:%M:%S'


def configure_logging(verbosity):
    logging_config = {
        'version': 1,
        'formatters': {
            'brief': {
                'format': LOGGING_FORMAT,
                'datefmt': LOGGING_DATEFMT,
            }
        },
        'handlers': {
            'brief': {
                'class': 'logging.StreamHandler',
                'formatter': 'brief',
            }
        },
        'loggers': {
            '': {  # root logger
                'level': logging.WARNING,
                'stream': sys.stdout,
                'handlers': ['brief',],
            },
            'Receiver': {
                'level': logging.WARNING,
                # 'stream': sys.stdout,

            }
        }
    }

    if verbosity == 1:
        logging_config['loggers']['']['level'] = logging.INFO
    elif verbosity >= 2:
        logging_config['loggers']['']['level'] = logging.DEBUG

    logging.config.dictConfig(logging_config)


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
