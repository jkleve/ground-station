from .events import ControlEvent, CommandEvent


# All inputs are values from -1.0 <= x <= 1.0
# Flight units for controls are 0 <= x <= 100
def convert_to_flight_units(x):
    return int(50*x + 50)


FULL_POSITIVE = convert_to_flight_units(1)
FULL_NEGATIVE = convert_to_flight_units(-1)
LEVEL = convert_to_flight_units(0)


flight_controls = {
    'keyboard': {
        'w': {  # key
            'key_down': (ControlEvent.PITCH, FULL_NEGATIVE),  # event. these take raw values
            'key_up': (ControlEvent.PITCH, LEVEL),  # event
        },
        's': {
            'key_down': (ControlEvent.PITCH, FULL_POSITIVE),
            'key_up': (ControlEvent.PITCH, LEVEL),
        },
        'a': {
            'key_down': (ControlEvent.ROLL, FULL_NEGATIVE),
            'key_up': (ControlEvent.ROLL, LEVEL),
        },
        'd': {
            'key_down': (ControlEvent.ROLL, FULL_POSITIVE),
            'key_up': (ControlEvent.ROLL, LEVEL),
        },
        'q': {
            'key_down': (ControlEvent.YAW, FULL_NEGATIVE),
            'key_up': (ControlEvent.YAW, LEVEL),
        },
        'e': {
            'key_down': (ControlEvent.YAW, FULL_POSITIVE),
            'key_up': (ControlEvent.YAW, LEVEL),
        },
        '1': {
            'key_down': (ControlEvent.THROTTLE, 10),
        },
        '2': {
            'key_down': (ControlEvent.THROTTLE, 20),
        },
        '3': {
            'key_down': (ControlEvent.THROTTLE, 30),
        },
        '4': {
            'key_down': (ControlEvent.THROTTLE, 40),
        },
        '5': {
            'key_down': (ControlEvent.THROTTLE, 50),
        },
        '6': {
            'key_down': (ControlEvent.THROTTLE, 60),
        },
        '7': {
            'key_down': (ControlEvent.THROTTLE, 70),
        },
        '8': {
            'key_down': (ControlEvent.THROTTLE, 80),
        },
        '9': {
            'key_down': (ControlEvent.THROTTLE, 90),
        },
        '0': {
            'key_down': (ControlEvent.THROTTLE, 100),
        },
        '`': {
            'key_down': (ControlEvent.THROTTLE, 0),
        },
        '\\': {
            'key_down': (ControlEvent.THROTTLE, 0),
        },
        'f': {
            'key_down': (CommandEvent.EXIT_FLIGHT_MODE, ),
        },
        'l': {
            'key_down': (CommandEvent.LEVEL_QUAD, ),  # TODO make second argument an array of data bytes. empty if none. then clean up command_handler
        },
    },
    'joystick': {
        'axis': {
            0: (ControlEvent.ROLL, convert_to_flight_units),  # this takes a callback
            1: (ControlEvent.PITCH, convert_to_flight_units),
            3: (ControlEvent.YAW, convert_to_flight_units),
            5: (ControlEvent.THROTTLE, convert_to_flight_units),
        },
        'buttons': {
        },
    },
}

non_flight_controls = {
    'keyboard': {
        '0': {
            'key_down': (ControlEvent.THROTTLE, 100),
        },
        '-': {
            'key_down': (ControlEvent.THROTTLE, 0),
        },
        'd': {
            'key_down': (CommandEvent.DONE, ),
        },
        'f': {
            'key_down': (CommandEvent.ENTER_FLIGHT_MODE, ),
        },
        'y': {
            'key_down': (CommandEvent.TOGGLE_YAWPITCHROLL, ),
        },
    },
    'joystick': {
        'axis': {
        },
        'buttons': {
        },
    },
}
