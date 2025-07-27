# system_state.py

_current_mode = 'NORMAL'

def get_mode():
    return _current_mode

def set_mode(mode):
    global _current_mode
    _current_mode = mode
    print(f"System mode set to: {_current_mode}")