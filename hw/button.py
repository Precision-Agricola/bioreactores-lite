# hw/button.py

import uasyncio as asyncio
from machine import Pin
from config.pins import BUTTON_PIN
from hw.relay_controller import controller as relays
from utils.logger import info, debug

_POLL_MS      = 10      # periodo de sondeo
_DEBOUNCE_MS  = 30      # tiempo estable requerido (≥30 ms)

class Button:
    def __init__(self, pin_no: int = BUTTON_PIN):
        self._pin   = Pin(pin_no, Pin.IN, Pin.PULL_UP)
        self._last  = self._pin.value()

    async def run(self):
        while True:
            val = self._pin.value()
            if val != self._last:                # cambio detectado
                await asyncio.sleep_ms(_DEBOUNCE_MS)
                if self._pin.value() == val:     # estable
                    if val == 0:                 # pulsador activo‑bajo
                        relays.toggle_pump()
                        info("Button → pump toggled")
                    else:
                        debug("Button released")
                    self._last = val
            await asyncio.sleep_ms(_POLL_MS)

button = Button()
