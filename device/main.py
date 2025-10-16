# device/main.py

import uasyncio
import time
import gc
from utils.logger import info, error
import system_state

CURRENT_MODE = system_state.get_mode()

if CURRENT_MODE == 'PROGRAM':
    info("Modo PROGRAM activo. No se inician tareas. REPL disponible.")
else:
    from machine import WDT
    from hw import button
    from tasks import control_task, display_task, sensor_task
    import web_server

    _START_TIME_FILE = "start_time.txt"
    _WDT_TIMEOUT_MS = 300000

    wdt = None
    try:
        wdt = WDT(timeout=_WDT_TIMEOUT_MS)
        info(f"Watchdog activado. Timeout: {_WDT_TIMEOUT_MS / 1000}s")
    except Exception as e:
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
    web_server.set_inoculation_start_time(start_timestamp)

    async def main():
        if CURRENT_MODE == 'EMERGENCY':
            info("!!! MODO EMERGENCIA ACTIVADO !!!")
            uasyncio.create_task(control_task._compressor_loop())
        else:
            info("Iniciando tareas de operación normal/demo...")
            
            control_task.start()
            display_task.start()
            sensor_task.start()
            uasyncio.create_task(button.button.run())

            info("Limpiando memoria antes de iniciar tareas de red...")
            gc.collect()
            info(f"Memoria libre: {gc.mem_free()} bytes")
            
            uasyncio.create_task(web_server.start_server())
            
            info("Todas las tareas principales han sido lanzadas.")

        while True:
            if wdt:
                wdt.feed()
            await uasyncio.sleep(60)

    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        info("Sistema detenido por el usuario.")
    finally:
        info("Finalizando ejecución.")
