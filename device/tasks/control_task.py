# tasks/control_task.py
import uasyncio as asyncio
from config import runtime
from hw.relay_controller import controller as relays
from utils.logger import info, warning
import system_state

async def _auto_pump_loop():
    is_demo = system_state.get_mode() == 'DEMO'
    info(f"Pump control task started in {system_state.get_mode()} mode.")

    if is_demo:
        interval_minutes = runtime.DEMO_AUTO_PUMP_INTERVAL_MIN
        duration_minutes = runtime.DEMO_AUTO_PUMP_DURATION_MIN
    else:
        interval_minutes = runtime.AUTO_PUMP_INTERVAL_MIN
        duration_minutes = runtime.AUTO_PUMP_DURATION_MIN

    while True:
        await asyncio.sleep(interval_minutes * 60)

        auto_turned_on = False
        if not relays.pump_is_on():
            info(f"Auto pump ON ({duration_minutes} min)")
            relays.toggle_pump()
            auto_turned_on = True

        await asyncio.sleep(duration_minutes * 60)

        if auto_turned_on and relays.pump_is_on():
            relays.toggle_pump()
            info("Auto pump OFF")
        elif auto_turned_on:
            warning("Auto routine expected to turn pump OFF, but it was already off.")

def start():
    info("Starting high-level control tasks...")
    asyncio.create_task(_auto_pump_loop())
