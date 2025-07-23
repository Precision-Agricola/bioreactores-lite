import uasyncio as asyncio
from machine import Pin
from config.pins import INDICATOR_PIN

_LEVELS = ("INFO", "WARNING", "ERROR")
_level_idx = 0
_pin = Pin(INDICATOR_PIN, Pin.OUT, value=0)

def set_level(level: str) -> None:
    global _level_idx
    lvl = level.upper()
    if lvl not in _LEVELS:
        raise ValueError("Indicator: invalid level '%s'" % level)
    _level_idx = _LEVELS.index(lvl)

async def _blink_loop() -> None:
   while True:
        if _level_idx == 0:
            _pin.off()
            await asyncio.sleep(0.2)

        elif _level_idx == 1:
            _pin.on()
            await asyncio.sleep(0.2)

        else:
            _pin.on()
            await asyncio.sleep(0.25)
            _pin.off()
            await asyncio.sleep(0.25)

def start() -> None:
    if not hasattr(start, "_task"):
        start._task = asyncio.create_task(_blink_loop())
