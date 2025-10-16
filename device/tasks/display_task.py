# device/tasks/display_task.py

import uasyncio as asyncio
from time import time
from hw.relay_controller import controller as relays
from ui.display import init as lcd_init, write
from tasks.sensor_task import current_readings

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
        
        level = current_readings["rs485"].get("level")
        level_line = f"Level: {level:.2f}m" if level is not None else "Level: ---"

        p32_val = current_readings["analog"].get("p32")
        analog_line = f"Ana1: {p32_val}" if p32_val is not None else "Ana1: ---"

        write((
            day_line,
            pump_line,
            level_line,
            analog_line
        ))
        await asyncio.sleep(3)

def start():
    lcd_init()
    asyncio.create_task(_loop())

def set_start_time(timestamp):
    global start_timestamp
    start_timestamp = timestamp
