# device/boot.py

import gc
import machine
import time
from config.pins import i2c, MODE_SW1_PIN, MODE_SW2_PIN
from utils.drivers.ds3231 import DS3231
import system_state

print("\n" + "="*40)
print("  BIOREACTOR IOT - INICIANDO SISTEMA")
print("="*40)

# --- Lógica de selección de modo ---
sw1_pin = machine.Pin(MODE_SW1_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
sw2_pin = machine.Pin(MODE_SW2_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
sw1, sw2 = sw1_pin.value(), sw2_pin.value()

# --- CAMBIO TEMPORAL PARA PRUEBAS ---
# Se fuerza el modo 'WORKING' para depurar el arranque del servidor web.
# TODO: Restaurar la lógica de switches una vez solucionado el problema.
system_state.set_mode('WORKING')
# La lógica original se deja comentada abajo para referencia.
# if sw1 and sw2:
#     system_state.set_mode('EMERGENCY')
# elif sw1:
#     system_state.set_mode('WORKING')
# elif sw2:
#     system_state.set_mode('DEMO')
# else:
#     system_state.set_mode('PROGRAM')
# -----------------------------------------

try:
    ds = DS3231(i2c())
    machine.RTC().datetime(ds.datetime())
    print("RTC Sincronizado:", time.localtime())
except Exception as e:
    print(f"ERROR: No se pudo inicializar el RTC. Detalle: {e}")

gc.collect()
print("-" * 40)
print(f"boot.py finalizado. Memoria libre: {gc.mem_free()} bytes.")
print("Cargando main.py...")
print("="*40)
