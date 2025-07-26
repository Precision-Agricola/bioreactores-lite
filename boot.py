# boot.py
import gc
import machine
import time
from config.pins import i2c, DIP_SWITCH_DEMO_PIN
from utils.drivers.ds3231 import DS3231
import system_state # Importamos nuestro nuevo módulo

print("\n" + "="*40)
print("  BIOREACTOR IOT - INICIANDO SISTEMA")
print("="*40)

dip_demo = machine.Pin(DIP_SWITCH_DEMO_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

if dip_demo.value() == 0:
    system_state.set_mode('DEMO')
else:
    system_state.set_mode('NORMAL')

try:
    ds = DS3231(i2c())
    machine.RTC().datetime(ds.datetime())
    print("RTC Sincronizado:", time.localtime())
except Exception as e:
    print(f"ERROR: No se pudo inicializar el RTC DS3231. Detalle: {e}")

gc.collect()
print("-" * 40)
print(f"boot.py finalizado. Memoria libre: {gc.mem_free()} bytes.")
print("Cargando main.py...")
print("="*40)
