# device/main.py

import uasyncio
import time
import gc
from utils.logger import info, error
import system_state
from machine import WDT

CURRENT_MODE = system_state.get_mode()

wdt = None
try:
    _WDT_TIMEOUT_MS = 300000
    wdt = WDT(timeout=_WDT_TIMEOUT_MS)
    info(f"Watchdog activado. Timeout: {_WDT_TIMEOUT_MS / 1000}s")
except Exception as e:
    error(f"No se pudo iniciar el watchdog: {e}")


async def main():
    
    if CURRENT_MODE == 'PROGRAM':
        info("Modo PROGRAM activo. Entrando en bucle inactivo.")
        info("REPL disponible. El WDT se está alimentando.")
        
        while True:
            if wdt:
                wdt.feed()
            await uasyncio.sleep(60)

    else:
        
        import web_server
        from tasks import display_task 

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
        web_server.set_inoculation_start_time(start_timestamp)

        if CURRENT_MODE == 'EMERGENCY':
            info("!!! MODO EMERGENCIA ACTIVADO !!!")
            from tasks import control_task
            uasyncio.create_task(control_task._compressor_loop())
        
        elif CURRENT_MODE == 'WORKING' or CURRENT_MODE == 'DEMO':
            info(f"Iniciando tareas de operación {CURRENT_MODE}...")
            
            info("Limpiando memoria antes de iniciar tareas de red...")
            gc.collect()
            info(f"Memoria libre: {gc.mem_free()} bytes")
            
            uasyncio.create_task(web_server.start_server())
            
            await uasyncio.sleep(2)

            info("Red iniciada. Importando módulos de tareas de bajo nivel...")
            from hw import button
            from tasks import control_task, sensor_task
            
            info("Iniciando tareas de bajo nivel (sensores, control, display)...")
            control_task.start()
            display_task.start()
            sensor_task.start()
            uasyncio.create_task(button.button.run())
            
            info("Todas las tareas principales han sido lanzadas.")

        info("Entrando en bucle principal (alimentando WDT).")
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
