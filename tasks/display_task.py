# tasks/display_task.py

import uasyncio as asyncio
from machine import ticks_ms, ticks_diff
from ui.display import init as lcd_init, write
from hw.relay_controller import controller as relays
from hw.relays import compressor_a, compressor_b

_BOOT_MS = ticks_ms()

async def _loop():
    while True:
        days = ticks_diff(ticks_ms(), _BOOT_MS) // 86_400_000 + 1

        pump_line = "Pump ON " if relays.pump_is_on() else "Pump OFF"

        h_a = compressor_a.hours() if compressor_a.is_on() else 0
        h_b = compressor_b.hours() if compressor_b.is_on() else 0

        write((
            f"Day {days}",
            pump_line,
            f"CompA {h_a:5.1f}h",
            f"CompB {h_b:5.1f}h",
        ))
        await asyncio.sleep(3)

def start():
    lcd_init()
    asyncio.create_task(_loop())
