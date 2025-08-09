# device/boot.py

import gc
import machine
import time
from config.pins import i2c, MODE_SW1_PIN, MODE_SW2_PIN
from utils.drivers.ds3231 import DS3231
import system_state

try:
    from config.system_version import VERSION, COMMIT, BUILD_DATE
except Exception:
    VERSION, COMMIT, BUILD_DATE = "dev", "local", "n/a"

print("\n" + "="*40)
print("  BIOREACTOR IOT - INICIANDO SISTEMA")
print("="*40)

# --- Lógica de selección de modo ---
sw1_pin = machine.Pin(MODE_SW1_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
sw2_pin = machine.Pin(MODE_SW2_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
sw1, sw2 = sw1_pin.value(), sw2_pin.value()


if sw1 and sw2:
    system_state.set_mode('EMERGENCY')
elif sw1:
    system_state.set_mode('WORKING')
elif sw2:
    system_state.set_mode('DEMO')
else:
    system_state.set_mode('PROGRAM')

try:
    ds = DS3231(i2c())
    machine.RTC().datetime(ds.datetime())
    print("RTC Sincronizado:", time.localtime())
except Exception as e:
    print(f"ERROR: No se pudo inicializar el RTC. Detalle: {e}")

gc.collect()

print("\n" + "="*40)
print("  BIOREACTOR INTELIGENTE PRECISIÓN AGRÍCOLA - INICIANDO SISTEMA")
print(f"  Version: {VERSION} ({COMMIT})")
print(f"  Build:   {BUILD_DATE} UTC")
print("="*40)
