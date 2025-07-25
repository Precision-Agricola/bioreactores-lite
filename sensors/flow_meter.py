# sensors/flow_meter.py

import uasyncio as asyncio
from machine import Pin
from time import ticks_ms, ticks_diff, sleep
from config.pins import FLOW_SENSOR_PIN
from utils.logger import debug

_FORMULAS = {
    "YF-B1": lambda f_hz: (f_hz + 3) / 11,
    "YF-B6": lambda f_hz:  f_hz / 6.6,
}
_MIN_GAP_MS = 2

class FlowMeter:
    def __init__(self, model="YF-B1"):
        self._to_lpm = _FORMULAS.get(model.upper(), _FORMULAS["YF-B1"])
        self._cnt    = 0
        self._last   = ticks_ms()
        Pin(FLOW_SENSOR_PIN, Pin.IN).irq(self._irq, Pin.IRQ_RISING)

    def _irq(self, pin):
        now = ticks_ms()
        if ticks_diff(now, self._last) >= _MIN_GAP_MS:
            self._cnt += 1
            self._last = now

    def litres_per_min(self, interval_s=1):
        start_cnt = self._cnt
        sleep(interval_s)
        pulses = self._cnt - start_cnt
        self._cnt = 0
        f_hz = pulses / interval_s
        return round(self._to_lpm(f_hz), 3)

    async def task(self, interval_s=5, cb=None):
        while True:
            await asyncio.sleep(interval_s)
            pulses = self._cnt
            self._cnt = 0
            lpm = self._to_lpm(pulses / interval_s)
            debug("Flow %.2f L/min" % lpm)
            if cb:
                cb(lpm)
