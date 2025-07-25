
from machine import Pin, SoftI2C

COMPRESSOR_A_PIN = 0    # IO0  – Compresor A
COMPRESSOR_B_PIN = 4    # IO4  – Compresor B
PUMP_RELAY_PIN = 14     # IO14 – Rele bomba
INDICATOR_PIN = 12      # IO12 – Indicador visual

FLOW_SENSOR_PIN = 19    # IO19 – Sensor de flujo
BUTTON_PIN = 18         # IO18 – Botón

SCL_PIN = 23
SDA_PIN = 21

def i2c(bus=0):
    return SoftI2C(bus, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
