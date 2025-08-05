# device/tasks/display_task.py

import uasyncio as asyncio
from time import time
from hw.relay_controller import controller as relays
from hw.relays import compressor_a, compressor_b
from ui.display import init as lcd_init, write

start_timestamp = 0

async def _loop():
    while True:
        if start_timestamp > 0:
            seconds_elapsed = time() - start_timestamp
            days = (seconds_elapsed // 86400) + 1
            day_line = f"Day {int(days)}"
        else:
            day_line = "RTC not set"

        pump_line = "Pump ON" if relays.pump_is_on() else "Pump OFF"

        h_a = compressor_a.hours()
        h_b = compressor_b.hours()

        write((
            day_line,
            pump_line,
            f"CompA {h_a:5.1f}h",
            f"CompB {h_b:5.1f}h",
        ))
        await asyncio.sleep(3)

def start():
    lcd_init()
    asyncio.create_task(_loop())

def set_start_time(timestamp):
    global start_timestamp
    start_timestamp = timestamp
