from argparse import ArgumentParser
from multiprocessing import Event, Process
import signal
import sys

from receiver import Receiver
from transmit import Transmitter
from utils import config_logs, connect

from mission.commands import Commanding
from mission.logs import get_logs


# import time
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
    parser.add_argument('-ms', '--milliseconds', action='store_true', help="Print time with milli-seconds")
    parser.add_argument('-u', '--uplink-frequency', type=int, default=10,
                        help="Uplink frequency in Hz (Default = 10 Hz)")

    args = parser.parse_args()

    config_logs(get_logs(args.milliseconds))

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
    commanding = Process(target=Commanding, args=(transmitter.send, args.uplink_frequency))

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
