# device/main.py

import uasyncio
import time
import gc
from utils.logger import info, error
import system_state
import web_server # <-- Mantenemos esta importación aquí
from machine import WDT # <-- Esta puede quedarse o moverse, es pequeña

CURRENT_MODE = system_state.get_mode()

if CURRENT_MODE == 'PROGRAM':
    info("Modo PROGRAM activo. No se inician tareas. REPL disponible.")
else:
    # --- CAMBIO: QUITAMOS LAS IMPORTACIONES DE TAREAS DE AQUÍ ---
    # from hw import button  <-- BORRAR
    # from tasks import control_task, display_task, sensor_task <-- BORRAR

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

    # Necesitamos display_task aquí, así que lo importamos justo a tiempo
    from tasks import display_task
    display_task.set_start_time(start_timestamp)
    web_server.set_inoculation_start_time(start_timestamp)

    async def main():
        if CURRENT_MODE == 'EMERGENCY':
            info("!!! MODO EMERGENCIA ACTIVADO !!!")
            # Importación justo a tiempo para el modo emergencia
            from tasks import control_task
            uasyncio.create_task(control_task._compressor_loop())
        else:
            info("Iniciando tareas de operación normal/demo...")
            
            info("Limpiando memoria antes de iniciar tareas de red...")
            gc.collect()
            info(f"Memoria libre: {gc.mem_free()} bytes")
            
            uasyncio.create_task(web_server.start_server())
            
            # Damos un pequeño respiro para que la tarea de red comience
            await uasyncio.sleep(2)

            # --- CAMBIO: IMPORTAR LOS MÓDULOS RESTANTES AQUÍ ---
            info("Red iniciada. Importando módulos de tareas de bajo nivel...")
            from hw import button
            from tasks import control_task, sensor_task
            
            info("Iniciando tareas de bajo nivel (sensores, control, display)...")
            control_task.start()
            display_task.start() # Ya fue importado antes
            sensor_task.start()
            uasyncio.create_task(button.button.run())
            
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
