from logging import DEBUG, INFO, WARNING, ERROR
import sys


def get_logs(log_ms=False):
    return ({
                'log_name': 'Receiver',
                'log_filename': 'logs/receiver.log',
                # 'log_stream': sys.stdout,
                'log_ms': log_ms,
                'stream_level': DEBUG,
                'file_level': DEBUG,
            },
            {
                'log_name': 'mission.packet_handlers',
                'log_filename': 'logs/packet_handler.log',
                'log_stream': sys.stdout,
                'stream_level': INFO,
                'log_ms': log_ms,
            },
            {
                'log_name': 'mission.packet',
                'log_filename': 'logs/packet.log',
                'log_stream': sys.stdout,
                'stream_level': INFO,
                'log_ms': log_ms,
            },
            {
                'log_name': 'Transmitter',
                'log_filename': 'logs/transmitter.log',
                'file_level': DEBUG,
                'log_ms': log_ms,
            },
            {
                'log_name': 'Commanding',
                'log_filename': 'logs/commanding.log',
                'log_stream': sys.stdout,
                'file_level': DEBUG,
                'stream_level': DEBUG,
                'log_ms': log_ms,
            },
            {
                'log_name': 'UserInput',
                'log_filename': 'logs/user_input.log',
                'file_level': DEBUG,
                # 'log_stream': sys.stdout,
                # 'stream_level': DEBUG,
                'log_ms': log_ms,
            },
            {
                'log_name': 'map_input',
                'log_filename': 'logs/user_input.log',
                'file_level': DEBUG,
                # 'log_stream': sys.stdout,
                # 'stream_level': DEBUG,
                'log_ms': log_ms,
            },
            {
                'log_name': 'ServiceManager',
                'log_filename': 'logs/services.log',
                'log_stream': sys.stdout,
                'file_level': DEBUG,
                'stream_level': INFO,
                'log_ms': log_ms,
            },
            {
                'log_name': 'ControlsService',
                'log_filename': 'logs/services.log',
                'file_level': DEBUG,
                # 'log_stream': sys.stdout,
                # 'stream_level': DEBUG,
                'log_ms': log_ms,
            },
            {
                'log_name': 'CommandsService',
                'log_filename': 'logs/services.log',
                'file_level': DEBUG,
                # 'log_stream': sys.stdout,
                # 'stream_level': DEBUG,
                'log_ms': log_ms,
            })

