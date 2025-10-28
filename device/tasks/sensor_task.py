# device/tasks/sensor_task.py

import uasyncio as asyncio
from machine import Pin, UART, ADC
import time
import struct
from utils.logger import info, error
from config import pins, sensor_params
from config.pins import i2c
from utils.drivers.ads1x15 import ADS1115

# --- Constantes (Sin cambios) ---
DO_ADC_RAW_MAX = 3722.0
DO_MG_L_MAX = 20.0
PH_SLOPE = 3.5 
PH_OFFSET = 0.0
ADC_MIN_RAW = 0.0
ADC_MAX_RAW = 32767.0
NH3_PPM_MIN = 1.0
NH3_PPM_MAX = 300.0
H2S_PPM_MIN = 0.5
H2S_PPM_MAX = 50.0
gain_index = 1

# --- CAMBIO 1: Diccionario de lecturas ---
# (Restauramos los placeholders de temperatura)
current_readings = {
    "analog": {
        "ph_value": None,
        "do_mg_l": None,
        "nh3_ppm": None,
        "s2h_ppm": None,
    },
    "rs485": {
        "level": None, # Ahora estará en CM
        "rs485_temperature": None, # Placeholder
        "ambient_temperature": None  # Placeholder
    }
}

# --- Clase HybridAnalogSensors (Sin cambios) ---
class HybridAnalogSensors:
    def __init__(self, i2c_bus, gain_index_val=1):
        try:
            self.adc_mux = ADS1115(i2c_bus, gain=gain_index_val)
            info(f"Sensor ADC ADS1115 (NH3/S2H) inicializado.")

            self.adc_ph = ADC(Pin(pins.PH_PIN))
            self.adc_ph.atten(ADC.ATTN_11DB)
            info(f"Sensor PH (ADC1 Pin {pins.PH_PIN}) inicializado.")

            self.adc_oxigeno = ADC(Pin(pins.OXIGENO_PIN))
            self.adc_oxigeno.atten(ADC.ATTN_11DB)
            info(f"Sensor Oxigeno (ADC1 Pin {pins.OXIGENO_PIN}) inicializado.")
            
        except Exception as e:
            error(f"No se pudo inicializar el hardware de sensores analógicos: {e}")
            raise

    def _map_value(self, x, in_min, in_max, out_min, out_max):
        if x < in_min: x = in_min
        if in_max == in_min: return out_min
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def read(self):
        try:
            raw_ph = self.adc_ph.read()
            raw_oxi = self.adc_oxigeno.read()
            raw_nh3 = self.adc_mux.read(rate=4, channel1=0)
            raw_s2h = self.adc_mux.read(rate=4, channel1=1)

            do_mg_l = self._map_value(raw_oxi, 0.0, DO_ADC_RAW_MAX, 0.0, DO_MG_L_MAX)
            v_ph = (raw_ph / 4095.0) * 3.3
            ph_value = (PH_SLOPE * v_ph) + PH_OFFSET
            ppm_nh3 = self._map_value(raw_nh3, ADC_MIN_RAW, ADC_MAX_RAW, NH3_PPM_MIN, NH3_PPM_MAX)
            ppm_s2h = self._map_value(raw_s2h, ADC_MIN_RAW, ADC_MAX_RAW, H2S_PPM_MIN, H2S_PPM_MAX)
            
            data = {
                "ph_value": ph_value,
                "do_mg_l": do_mg_l,
                "nh3_ppm": ppm_nh3,
                "s2h_ppm": ppm_s2h,
            }
            return data
        except Exception as e:
            error(f"Error al leer sensores analógicos (híbrido): {e}")
            return None

# --- Clase RS485Sensor (MODIFICADA) ---
class RS485Sensor:
    def __init__(self):
        try:
            Pin(sensor_params.RS485_RX, Pin.IN, Pin.PULL_UP)
            self.uart = UART(2, baudrate=9600, tx=sensor_params.RS485_TX, rx=sensor_params.RS485_RX)
            self.de_re = Pin(sensor_params.RS485_DE_RE, Pin.OUT)
            self.de_re.off()
            info("Sensor RS485 (QDY30A - Modo Entero) inicializado.")
        except Exception as e:
            error(f"No se pudo inicializar la UART para RS485: {e}")
            raise

        self.commands = [ b'\x01\x03\x00\x04\x00\x01\xC5\xCB' ]
        self.valid_ranges = { "level": (-2.0, 550.0) } # Rango en CM

    def _send(self, cmd):
        try:
            self.uart.read(self.uart.any())
            self.de_re.on()
            self.uart.write(cmd)
            time.sleep_ms(10)
            self.de_re.off()
            time.sleep_ms(300) # Espera aumentada
            return self.uart.read(20)
        except Exception as e:
            error(f"Error en envío RS485: {e}")
            return None

    def _decode(self, resp):
        if not resp or len(resp) < 7 or resp[2] != 0x02:
            return None
        try:
            raw_int = struct.unpack('>H', resp[3:5])[0]
            val_cm = raw_int / 10.0 # Valor en CM (ej: 194 -> 19.4)
            return val_cm
        except Exception as e:
            error(f"Error en decodificación RS485 (int): {e}")
            return None

    def _get_reading(self, cmd, param, attempts=3):
        vals = []
        for _ in range(attempts):
            val = self._decode(self._send(cmd))
            if val is not None:
                min_v, max_v = self.valid_ranges.get(param, (-1e10, 1e10))
                if min_v <= val <= max_v:
                    vals.append(val)
            time.sleep_ms(200)
        return sorted(vals)[len(vals)//2] if vals else None

    # --- CAMBIO 2: Retornar diccionario completo ---
    def read(self):
        level_val_cm = self._get_reading(self.commands[0], "level")
        
        # Devolvemos el diccionario completo.
        # 'level' ahora está en CM.
        return {
            "level": level_val_cm, 
            "rs485_temperature": None, # Placeholder
            "ambient_temperature": None # Placeholder
        }

# --- Bucle _loop (MODIFICADO) ---
async def _loop():
    rs485_reader = None
    analog_reader = None
    
    try:
        i2c_bus = i2c()
        info("Bus I2C para sensores inicializado.")
        analog_reader = HybridAnalogSensors(i2c_bus, gain_index_val=gain_index)
    except Exception as e:
        error(f"Fallo al inicializar sensores analógicos: {e}")

    if sensor_params.ENABLE_RS485:
        try:
            rs485_reader = RS485Sensor()
            info("Módulo RS485 HABILITADO.")
        except Exception as e:
            rs485_reader = None
            # Ya no escribimos en 'rs485_status'
            error(f"Fallo al inicializar RS485: {e}")
    else:
        info("Módulo RS485 DESHABILITADO por configuración.")
    
    info(f"Tarea de sensores iniciada. Intervalo de lectura: 15s")

    while True:
        if analog_reader:
            analog_data = analog_reader.read()
            if analog_data:
                current_readings["analog"].update(analog_data)
                info(f"Lecturas Analógicas: {current_readings['analog']}")

        if rs485_reader:
            # .read() ahora devuelve el dict completo
            rs485_data = rs485_reader.read()
            current_readings["rs485"].update(rs485_data)
            info(f"Lecturas RS485: {current_readings['rs485']}")
        
        await asyncio.sleep(15)

def start():
    info("Lanzando tarea de control de sensores...")
    asyncio.create_task(_loop())
