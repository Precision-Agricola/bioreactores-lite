# sensors/flow_meter.py

import uasyncio as asyncio
from machine import Pin
import machine
from time import ticks_ms, ticks_diff
from config.pins import FLOW_SENSOR_PIN
from utils.logger import debug

_FORMULAS = {
    "YF-B1": lambda f_hz: (f_hz + 3) / 11,
    "YF-B6": lambda f_hz: f_hz / 6.6,
}
_MIN_GAP_MS = 2

class FlowMeter:
    def __init__(self, model="YF-B1"):
        self._to_lpm = _FORMULAS.get(model.upper(), _FORMULAS["YF-B1"])
        self._cnt = 0
        self._last = ticks_ms()
        pin = Pin(FLOW_SENSOR_PIN, Pin.IN, Pin.PULL_UP)
        pin.irq(self._irq, Pin.IRQ_RISING)

    def _irq(self, pin):
        now = ticks_ms()
        if ticks_diff(now, self._last) >= _MIN_GAP_MS:
            self._cnt += 1
            self._last = now

    async def task(self, interval_s=5, cb=None):
        while True:
            await asyncio.sleep(interval_s)
            irq_state = machine.disable_irq()
            pulses = self._cnt
            self._cnt = 0
            machine.enable_irq(irq_state)
            f_hz = pulses / interval_s
            lpm = self._to_lpm(f_hz)
            debug("Flow %.2f L/min" % lpm)
            if cb:
                cb(lpm)
