# main.py

import uasyncio
import time
import uos
from utils.logger import info, error

from hw import button
from hw.relay_controller import controller as relays
from sensors.flow_meter import FlowMeter
from tasks import control_task, display_task

_START_TIME_FILE = "start_time.txt"

start_timestamp = 0
try:
    with open(_START_TIME_FILE, "r") as f:
        start_timestamp = int(f.read())
    info(f"Timestamp de inicio leído: {start_timestamp}")

except OSError:
    info("Primer arranque detectado. Creando archivo de tiempo de inicio.")
    try:
        start_timestamp = time.time()
        with open(_START_TIME_FILE, "w") as f:
            f.write(str(start_timestamp))
        info(f"Timestamp de inicio guardado: {start_timestamp}")
    except Exception as e:
        error(f"No se pudo crear el archivo de inicio: {e}")

display_task.set_start_time(start_timestamp)


async def main():
    info("Iniciando todas las tareas del sistema...")

    flow_meter = FlowMeter()

    control_task.start()
    display_task.start()

    uasyncio.create_task(button.button.run())
    uasyncio.create_task(flow_meter.task())

    info("Todas las tareas han sido lanzadas.")

    while True:
        await uasyncio.sleep(60)

try:
    uasyncio.run(main())
except KeyboardInterrupt:
    info("Sistema detenido por el usuario.")
finally:
    relays.set_light(False) # Apaga el indicador
    uasyncio.new_event_loop()
    info("Bucle de eventos reiniciado. Adiós.")
