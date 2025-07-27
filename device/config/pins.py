# config/pins

from machine import Pin, SoftI2C

COMPRESSOR_A_PIN = 2    # IO2  – Compresor A
COMPRESSOR_B_PIN = 4    # IO4  – Compresor B
PUMP_RELAY_PIN = 14     # IO14 – Rele bomba - RELAY CHANNEL 2
INDICATOR_PIN = 12      # IO12 – Indicador visual - RELAY CHANNEL 3

FLOW_SENSOR_PIN = 18    # IO19 – Sensor de flujo
BUTTON_PIN = 19         # IO18 – Botón

SCL_PIN = 23
SDA_PIN = 21

MODE_SW1_PIN = 25  # Pin para activar el MODO DEMO
MODE_SW2_PIN= 26 # Pin de repuesto para futuros modos

def i2c():
    return SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
