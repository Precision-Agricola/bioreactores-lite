# hw/relays

from machine import Pin
from time import ticks_ms, ticks_diff
from config.pins import (
    INDICATOR_PIN,
    COMPRESSOR_A_PIN,
    COMPRESSOR_B_PIN,
    PUMP_RELAY_PIN,
)

class Relay:
    def __init__(self, pin_no: int, *, active_high: bool = False):
        # OFF al arranque
        self._pin = Pin(pin_no, Pin.OUT, value=0 if active_high else 1)
        self._ah   = active_high
        self._on   = False
        self._ts   = None
        self._sec  = 0

    def on(self):
        self._pin.value(1 if self._ah else 0)
        if not self._on:
            self._on, self._ts = True, ticks_ms()

    def off(self):
        self._pin.value(0 if self._ah else 1)
        if self._on:
            self._sec += ticks_diff(ticks_ms(), self._ts) // 1000
            self._on, self._ts = False, None

    def toggle(self):
        (self.off if self._on else self.on)()

    def is_on(self):
        return self._on

    def hours(self):
        sec = self._sec
        if self._on:
            sec += ticks_diff(ticks_ms(), self._ts) // 1000
        return sec / 3600

# Instancias globales (singletons)
compressor_a = Relay(COMPRESSOR_A_PIN)
compressor_b = Relay(COMPRESSOR_B_PIN)
pump_relay   = Relay(PUMP_RELAY_PIN, active_high=True)
indicator_rl = Relay(INDICATOR_PIN)
