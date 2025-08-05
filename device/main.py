# main.py
import uasyncio
import time
import uos
from machine import WDT
from utils.logger import info, error
import system_state

# --- Hardware & Sensores ---
from hw import button
from hw.relay_controller import controller as relays
from sensors.flow_meter import flow_meter # Importamos la instancia global

# --- Tareas ---
from tasks import control_task, display_task
import web_server # Importamos el nuevo módulo del servidor

# --- Constantes ---
_START_TIME_FILE = "start_time.txt"
_WDT_TIMEOUT_MS = 300000
_WEB_SERVER_START_DELAY_S = 10 # Nuevo: Retardo para iniciar el servidor

# --- Inicialización del Watchdog ---
try:
    wdt = WDT(timeout=_WDT_TIMEOUT_MS)
    info(f"Watchdog activado. Timeout: {_WDT_TIMEOUT_MS / 1000}s")
except Exception as e:
    wdt = None
    error(f"No se pudo iniciar el watchdog: {e}")

# --- Manejo del Tiempo de Arranque ---
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

# --- Tarea de arranque retardado para el servidor web ---
async def start_web_server_with_delay():
    """Espera un tiempo para que el sistema se estabilice antes de iniciar el Wi-Fi."""
    info(f"El servidor web se iniciará en {_WEB_SERVER_START_DELAY_S} segundos...")
    await uasyncio.sleep(_WEB_SERVER_START_DELAY_S)
    await web_server.start_server()

# --- Función Principal Asíncrona ---
async def main():

    CURRENT_MODE = system_state.get_mode()

    if CURRENT_MODE == 'EMERGENCY':
        info("!!! MODO EMERGENCIA ACTIVADO !!!")
        info("Ejecutando alternancia de aireadores cada 3 horas.")
        uasyncio.create_task(control_task._compressor_loop())
    elif CURRENT_MODE != 'PROGRAM':
        info("Iniciando tareas de operación normal/demo...")
        
        # Tareas de control y hardware
        control_task.start()
        display_task.start()
        uasyncio.create_task(button.button.run())
        uasyncio.create_task(flow_meter.task())

        # NUEVO: Iniciar el servidor web con retardo
        uasyncio.create_task(start_web_server_with_delay())
        
        info("Todas las tareas principales han sido lanzadas.")

    # Bucle principal de alimentación del watchdog
    while True:
        if wdt:
            wdt.feed()
        await uasyncio.sleep(60)


# --- Punto de Entrada ---
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
