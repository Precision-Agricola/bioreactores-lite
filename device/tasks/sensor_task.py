# device/tasks/sensor_task.py

import uasyncio as asyncio
from machine import Pin, UART, ADC
import time
import struct
from utils.logger import info, error
from config import pins, sensor_params
from config.pins import i2c
from utils.drivers.ads1x15 import ADS1115

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

current_readings = {
    "analog": {
        "ph_value": None,
        "do_mg_l": None,
        "nh3_ppm": None,
        "s2h_ppm": None,
    },
    "rs485": {
        "level": None,
        "rs485_temperature": None,
        "ambient_temperature": None
    }
}

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
            
            time.sleep_ms(50) 
            raw_nh3 = self.adc_mux.read(rate=4, channel1=0)
            time.sleep_ms(50)
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

class RS485Sensor:
    def __init__(self):
        try:
            Pin(sensor_params.RS485_RX, Pin.IN, Pin.PULL_UP)
            self.uart = UART(2, baudrate=9600, tx=sensor_params.RS485_TX, rx=sensor_params.RS485_RX)
            self.de_re = Pin(sensor_params.RS485_DE_RE, Pin.OUT)
            self.de_re.off()
            info("Sensor RS485 (Nivel+Temp) inicializado.")
        except Exception as e:
            error(f"No se pudo inicializar la UART para RS485: {e}")
            raise

        self.commands = [ 
            b'\x01\x03\x00\x04\x00\x02\x85\xCA'
        ]
        self.valid_ranges = { 
            "level": (-2.0, 1050.0),
            "rs485_temperature": (-10.0, 100.0)
        }

    def _send(self, cmd):
        try:
            self.uart.read(self.uart.any())
            self.de_re.on()
            self.uart.write(cmd)
            time.sleep_ms(10)
            self.de_re.off()
            time.sleep_ms(300)
            return self.uart.read(20)
        except Exception as e:
            error(f"Error en envío RS485: {e}")
            return None

    def _decode(self, resp):
        if not resp or len(resp) < 9 or resp[2] != 0x04:
            return None, None
        try:
            level_mm = struct.unpack('>H', resp[3:5])[0]
            val_cm = level_mm / 10.0
            
            temp_raw = struct.unpack('>H', resp[5:7])[0]
            val_temp_c = temp_raw / 10.0
            
            return val_cm, val_temp_c
        except Exception as e:
            error(f"Error en decodificación RS485 (dual): {e}")
            return None, None

    def _get_reading(self, cmd, params, attempts=3):
        vals_level = []
        vals_temp = []
        
        for _ in range(attempts):
            level, temp = self._decode(self._send(cmd))
            
            if level is not None:
                min_v, max_v = self.valid_ranges.get(params[0], (-1e10, 1e10))
                if min_v <= level <= max_v:
                    vals_level.append(level)
            
            if temp is not None:
                min_v, max_v = self.valid_ranges.get(params[1], (-1e10, 1e10))
                if min_v <= temp <= max_v:
                    vals_temp.append(temp)
            
            time.sleep_ms(200)
        
        level_final = sorted(vals_level)[len(vals_level)//2] if vals_level else None
        temp_final = sorted(vals_temp)[len(vals_temp)//2] if vals_temp else None
        
        return level_final, temp_final

    def read(self):
        level_val_cm, temp_val_c = self._get_reading(
            self.commands[0], 
            ("level", "rs485_temperature")
        )
        
        return {
            "level": level_val_cm, 
            "rs485_temperature": temp_val_c,
            "ambient_temperature": None
        }

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
            rs485_data = rs485_reader.read()
            current_readings["rs485"].update(rs485_data)
            info(f"Lecturas RS485: {current_readings['rs485']}")
        
        await asyncio.sleep(15)

def start():
    info("Lanzando tarea de control de sensores...")
    asyncio.create_task(_loop())
