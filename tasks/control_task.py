import uasyncio as asyncio
from machine import Pin, ticks_ms, ticks_diff
from config.pins import BUTTON_PIN
from config.runtime import AUTO_PUMP_INTERVAL_MIN, AUTO_PUMP_DURATION_MIN
from hw.relay_controller import controller as relays
from utils.logger import info, warning

_POLL_MS      = 10
_DEBOUNCE_MS  = 30

async def _button_loop():
    btn = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    last = btn.value()
    while True:
        v = btn.value()
        if v != last:
            await asyncio.sleep_ms(_DEBOUNCE_MS)
            if btn.value() == v and v == 0:
                relays.toggle_pump()
                info("Button → pump toggled (manual override)")
            last = v
        await asyncio.sleep_ms(_POLL_MS)

async def _auto_loop():
    while True:
        await asyncio.sleep(AUTO_PUMP_INTERVAL_MIN * 60)

        if not relays.pump_is_on():
            info("Auto pump ON")
            relays.toggle_pump()
            auto_on = True
        else:
            auto_on = False

        await asyncio.sleep(AUTO_PUMP_DURATION_MIN * 60)

        if auto_on and relays.pump_is_on():
            relays.toggle_pump()
            info("Auto pump OFF")
        elif auto_on:
            warning("Auto cycle wanted OFF but pump already changed")

def start():
    asyncio.create_task(_button_loop())
    asyncio.create_task(_auto_loop())
