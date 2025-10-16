# device/config/pins

from machine import Pin, SoftI2C

COMPRESSOR_A_PIN = [27,12]    #   – Compresor A
COMPRESSOR_B_PIN = [14,13]    #   – Compresor B
PUMP_RELAY_PIN = 15    # I15 – Rele solido

BUTTON_PIN = 19         # IO19 – Botón

SCL_PIN = 23
SDA_PIN = 21

MODE_SW1_PIN = 25  # Pin para activar el MODO DEMO
MODE_SW2_PIN= 26 # Pin de repuesto para futuros modos

# --- Sensores analógicos ---
PH_SENSOR_PIN  = 32  # pH
O2_SENSOR_PIN  = 33  # Oxígeno disuelto
NH3_SENSOR_PIN = 2   # Amoniaco (NH3)
H2S_SENSOR_PIN = 4   # Sulfuro de hidrógeno (H2S)

def i2c():
    return SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
