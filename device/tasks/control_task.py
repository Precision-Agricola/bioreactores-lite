# device/tasks/control_task.py

import uasyncio as asyncio
from config import runtime
from hw.relay_controller import controller as relays
from utils.logger import info
from sensors.analog_readings import read_relatives as read_analog  # <— IMPORT CORRECTO
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


async def _analog_loop():
    """
    Lectura periódica de sensores analógicos (pH, O2, NH3, H2S)
    Solo activa en modo DEMO o WORK.
    """
    mode = system_state.get_mode()
    if mode not in ('DEMO', 'WORK'):
        return  # No ejecuta en PROGRAM ni EMERGENCY

    info(f"Sensor loop activo en modo: {mode}")

    while True:
        vals = read_analog()  # {'pH': float, 'O2_mgL': float, 'NH3_pct': float, 'H2S_pct': float}
        info(
            "pH: {:.2f} | O2: {:.2f} mg/L | NH3: {:.1f}% | H2S: {:.1f}%"
            .format(vals['pH'], vals['O2_mgL'], vals['NH3_pct'], vals['H2S_pct'])
        )
        await asyncio.sleep(30)  # cada 30 s


def start():
    info("Starting high-level control tasks...")
    asyncio.create_task(_auto_pump_loop())
    asyncio.create_task(_compressor_loop())
    asyncio.create_task(_analog_loop())
