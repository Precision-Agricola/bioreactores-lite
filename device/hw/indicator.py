# device/hw/indicator.py

import uasyncio as asyncio
from machine import Pin
from config.pins import INDICATOR_PIN

_LEVELS = ("INFO", "WARNING", "ERROR")
_level_idx = 0
_pin = Pin(INDICATOR_PIN, Pin.OUT, value=0)
_task = None

def set_level(level: str):
    global _level_idx
    try:
        _level_idx = _LEVELS.index(level.upper())
    except ValueError:
        raise ValueError("Indicator: invalid level '%s'" % level)

async def _blink_loop():
    while True:
        if _level_idx == 0:
            _pin.off(); await asyncio.sleep(0.2)
        elif _level_idx == 1:
            _pin.on();  await asyncio.sleep(0.2)
        else:
            _pin.on();  await asyncio.sleep(0.25)
            _pin.off(); await asyncio.sleep(0.25)

def start():
    global _task
    if _task is None:
        _task = asyncio.create_task(_blink_loop())
