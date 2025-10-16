# device/hw/relays.py

from machine import Pin
from time import ticks_ms, ticks_diff
from config.pins import (
    COMPRESSOR_A_PIN,
    COMPRESSOR_B_PIN,
    PUMP_RELAY_PIN,
)

class Relay:
    def __init__(self, pin_no: int, *, active_high: bool = False):
        # Por defecto, la mayoría de módulos de relé trabajan activos en bajo
        # (active_high=False). Si tu módulo se activa con 1 lógico, cámbialo a True.
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


class GroupRelay:
    """Controla varios pines como un solo relevador lógico (p.ej. 2 por compresor)."""
    def __init__(self, pins, *, active_high: bool = False):
        self._relays = [Relay(p, active_high=active_high) for p in pins]

    def on(self):
        for r in self._relays:
            r.on()

    def off(self):
        for r in self._relays:
            r.off()

    def toggle(self):
        if self.is_on():
            self.off()
        else:
            self.on()

    def is_on(self):
        return any(r.is_on() for r in self._relays)

    def hours(self):
        if not self._relays:
            return 0.0
        return sum(r.hours() for r in self._relays) / len(self._relays)


# ==== Instancias ====
compressor_a = GroupRelay(COMPRESSOR_A_PIN, active_high=True)
compressor_b = GroupRelay(COMPRESSOR_B_PIN, active_high=True)
pump_relay   = Relay(PUMP_RELAY_PIN, active_high=True)
