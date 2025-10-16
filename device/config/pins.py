# device/config/pins.py
from machine import Pin, SoftI2C

COMPRESSOR_A_PIN = [27,12]    #    – Compresor A
COMPRESSOR_B_PIN = [14,13]    #    – Compresor B
PUMP_RELAY_PIN = 15     # I15 – Rele solido

BUTTON_PIN = 19         # IO19 – Botón

SCL_PIN = 23
SDA_PIN = 21

MODE_SW1_PIN = 25   # Pin para activar el MODO DEMO
MODE_SW2_PIN = 26   # Pin de repuesto para futuros modos

ANALOG_PIN_1 = 32
ANALOG_PIN_2 = 33
ANALOG_PIN_3 = 2
ANALOG_PIN_4 = 4

def i2c():
    return SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
