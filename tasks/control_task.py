# tasks/control_task.py

import uasyncio as asyncio
from config.runtime import AUTO_PUMP_INTERVAL_MIN, AUTO_PUMP_DURATION_MIN
from hw.relay_controller import controller as relays
from utils.logger import info, warning

async def _auto_pump_loop():
   while True:
        await asyncio.sleep(AUTO_PUMP_INTERVAL_MIN * 60)

        auto_turned_on = False

        if not relays.pump_is_on():
            info("Auto pump routine: Turning ON")
            relays.toggle_pump()
            auto_turned_on = True

        await asyncio.sleep(AUTO_PUMP_DURATION_MIN * 60)

        if auto_turned_on and relays.pump_is_on():
            relays.toggle_pump()
            info("Auto pump routine: Turning OFF")
        elif auto_turned_on:
            warning("Auto routine expected to turn pump OFF, but it was already off.")

def start():
    info("Starting high-level control tasks...")
    asyncio.create_task(_auto_pump_loop())
