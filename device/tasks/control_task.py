# device/tasks/control_task.py

import uasyncio as asyncio
from config import runtime
from hw.relay_controller import controller as relays
from utils.logger import info
import system_state

async def _auto_pump_loop():
    time_factor = system_state.get_time_factor()
    
    interval_seconds = (runtime.AUTO_PUMP_INTERVAL_MIN * 60) // time_factor
    duration_seconds = (runtime.AUTO_PUMP_DURATION_MIN * 60) // time_factor

    info(f"Pump task started. Interval: {interval_seconds}s, Duration: {duration_seconds}s")

    while True:
        await asyncio.sleep(interval_seconds)
        
        auto_turned_on = False
        if not relays.pump_is_on():
            info(f"Auto pump ON (for {duration_seconds}s)")
            relays.toggle_pump()
            auto_turned_on = True
        
        await asyncio.sleep(duration_seconds)
        
        if auto_turned_on and relays.pump_is_on():
            relays.toggle_pump()
            info("Auto pump OFF")

async def _compressor_loop():
    time_factor = system_state.get_time_factor()
    
    cycle_seconds = (runtime.COMPRESSOR_CYCLE_HOURS * 3600) // time_factor
    
    info(f"Compressor task started. Cycle duration: {cycle_seconds}s per compressor.")

    while True:
        info("Activando Compresor A.")
        relays.set_compressors(a_on=True)
        await asyncio.sleep(cycle_seconds)

        info("Activando Compresor B.")
        relays.set_compressors(a_on=False)
        await asyncio.sleep(cycle_seconds)

def start():
    info("Starting high-level control tasks...")
    asyncio.create_task(_auto_pump_loop())
    asyncio.create_task(_compressor_loop())
