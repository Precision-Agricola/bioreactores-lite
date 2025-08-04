# device/main.py

import uasyncio
import time
import uos
from machine import WDT
from utils.logger import info, error
import system_state

from hw import button
from hw.relay_controller import controller as relays
from sensors.flow_meter import FlowMeter
from tasks import control_task, display_task

_START_TIME_FILE = "start_time.txt"
_WDT_TIMEOUT_MS = 300000

try:
    wdt = WDT(timeout=_WDT_TIMEOUT_MS)
    info(f"Watchdog activado. Timeout: {_WDT_TIMEOUT_MS / 1000}s")
except Exception as e:
    wdt = None
    error(f"No se pudo iniciar el watchdog: {e}")


start_timestamp = 0
try:
    with open(_START_TIME_FILE, "r") as f:
        start_timestamp = int(f.read())
except OSError:
    info("Primer arranque detectado. Creando archivo de tiempo de inicio.")
    try:
        start_timestamp = time.time()
        with open(_START_TIME_FILE, "w") as f: f.write(str(start_timestamp))
    except Exception as e:
        error(f"No se pudo crear el archivo de inicio: {e}")
display_task.set_start_time(start_timestamp)

async def main():
    """Función principal que lanza tareas y supervisa el sistema."""
    CURRENT_MODE = system_state.get_mode()

    if CURRENT_MODE == 'EMERGENCY':
        info("!!! MODO EMERGENCIA ACTIVADO !!!")
        info("Ejecutando alternancia de aireadores cada 3 horas.")
        uasyncio.create_task(control_task._compressor_loop())

    elif CURRENT_MODE != 'PROGRAM':
        info("Iniciando tareas de operación normal/demo...")
        flow_meter = FlowMeter()
        control_task.start()
        display_task.start()
        uasyncio.create_task(button.button.run())
        uasyncio.create_task(flow_meter.task())
        info("Todas las tareas han sido lanzadas.")

    while True:
        if wdt:
            wdt.feed()
        await uasyncio.sleep(60)

CURRENT_MODE = system_state.get_mode()

if CURRENT_MODE == 'PROGRAM':
    info("Modo PROGRAM activo. No se inician tareas. REPL disponible.")
else:
    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        info("Sistema detenido por el usuario.")
    finally:
        info("Finalizando ejecución.")
