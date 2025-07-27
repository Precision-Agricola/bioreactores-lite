# main.py

import uasyncio
import time
import uos
from utils.logger import info, error
import system_state

from hw import button
from hw.relay_controller import controller as relays
from sensors.flow_meter import FlowMeter
from tasks import control_task, display_task

_START_TIME_FILE = "start_time.txt"

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

async def emergency_loop():
    """Bucle simple y robusto para el modo de emergencia."""
    info("!!! MODO EMERGENCIA ACTIVADO !!!")
    info("Ejecutando alternancia de aireadores cada 3 horas.")
    while True:
        relays.set_compressors(a_on=True)
        info("EMERGENCIA: Aireador A ENCENDIDO.")
        await uasyncio.sleep(3 * 3600) # Espera 3 horas

        relays.set_compressors(a_on=False)
        info("EMERGENCIA: Aireador B ENCENDIDO.")
        await uasyncio.sleep(3 * 3600) # Espera 3 horas

async def normal_operation_loop():
    """Bucle para operación normal y demo, inicia todas las tareas."""
    info("Iniciando todas las tareas del sistema...")
    flow_meter = FlowMeter()
    control_task.start()
    display_task.start()
    uasyncio.create_task(button.button.run())
    uasyncio.create_task(flow_meter.task())
    info("Todas las tareas han sido lanzadas.")
    while True:
        await uasyncio.sleep(60)

CURRENT_MODE = system_state.get_mode()

try:
    if CURRENT_MODE == 'EMERGENCY':
        uasyncio.run(emergency_loop())
        
    elif CURRENT_MODE == 'PROGRAM':
        info("Modo PROGRAM activo. No se inician tareas.")
        info("REPL disponible para programación.")
        
    else:
        uasyncio.run(normal_operation_loop())

except KeyboardInterrupt:
    info("Sistema detenido por el usuario.")
finally:
    info("Finalizando ejecución.")
