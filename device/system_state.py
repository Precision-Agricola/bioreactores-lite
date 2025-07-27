# system_state.py

from config import runtime

_current_mode = 'NORMAL'

def set_mode(mode):
    global _current_mode
    _current_mode = mode
    print(f"System mode set to: {_current_mode}")

def get_mode():
    return _current_mode

def get_time_factor():
    if get_mode() == 'DEMO':
        return runtime.DEMO_TIME_FACTOR
    else:
        return 1
