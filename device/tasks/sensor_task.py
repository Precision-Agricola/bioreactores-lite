# device/tasks/sensor_task.py

import uasyncio as asyncio
from machine import Pin, UART, ADC
import time
import struct
from utils.logger import info, error
from config import pins, sensor_params
from config.pins import i2c
from utils.drivers.ads1x15 import ADS1115

ADC_MIN_RAW = 0.0
ADC_MAX_RAW = 32767.0

NH3_PPM_MIN = 1.0
NH3_PPM_MAX = 300.0

H2S_PPM_MIN = 0.5
H2S_PPM_MAX = 50.0

gain_index = 1 

current_readings = {
    "analog": {
        "ph": None,         # Pin 32 (ADC1) - Crudo
        "oxigeno": None,    # Pin 33 (ADC1) - Crudo
        "nh3_ppm": None,    # Mux I2C Canal 0 - Convertido a PPM
        "s2h_ppm": None,    # Mux I2C Canal 1 - Convertido a PPM
    },
    "rs485": {
        "level": None, "rs485_temperature": None, "ambient_temperature": None,
    }
}

class HybridAnalogSensors:
    """Lee de 2 ADC internos (PH, Oxi) y del ADC I2C (NH3, S2H)."""
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
        """Mapea un valor de un rango a otro, linealmente."""
        if x < in_min:
            x = in_min
        if in_max == in_min:
            return out_min
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def read(self):
        """Lee todos los sensores y aplica la conversión lineal a los de I2C."""
        try:
            raw_nh3 = self.adc_mux.read(rate=4, channel1=0)
            raw_s2h = self.adc_mux.read(rate=4, channel1=1)

            ppm_nh3 = self._map_value(raw_nh3, ADC_MIN_RAW, ADC_MAX_RAW, NH3_PPM_MIN, NH3_PPM_MAX)
            ppm_s2h = self._map_value(raw_s2h, ADC_MIN_RAW, ADC_MAX_RAW, H2S_PPM_MIN, H2S_PPM_MAX)

            data = {
                "ph": self.adc_ph.read(),
                "oxigeno": self.adc_oxigeno.read(),
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
            info("Sensor RS485 inicializado.")
        except Exception as e:
            error(f"No se pudo inicializar la UART para RS485: {e}")
            raise

        self.commands = [
            b'\x01\x03\x04\x0a\x00\x02\xE5\x39',
            b'\x01\x03\x04\x08\x00\x02\x44\xF9',
            b'\x01\x03\x04\x0c\x00\x02\x05\x38'
        ]
        self.valid_ranges = {
            "level": (-0.1, 3.0),
            "rs485_temperature": (-10, 350),
            "ambient_temperature": (0, 50)
        }

    def _send(self, cmd):
        try:
            self.uart.read(self.uart.any())
            self.de_re.on()
            self.uart.write(cmd)
            time.sleep_ms(10)
            self.de_re.off()
            time.sleep_ms(200)
            return self.uart.read(20)
        except Exception as e:
            error(f"Error en envío RS485: {e}")
            return None

    def _decode(self, resp):
        if not resp or len(resp) < 7: return None
        try:
            if resp[:3] == b'\x01\x03\x04':
                return struct.unpack('>f', resp[3:7])[0]
        except Exception as e:
            error(f"Error en decodificación RS485: {e}")
        return None

    def _get_reading(self, cmd, param, attempts=3):
        vals = []
        for _ in range(attempts):
            val = self._decode(self._send(cmd))
            if val is not None:
                min_v, max_v = self.valid_ranges.get(param, (-1e10, 1e10))
                if min_v <= val <= max_v and abs(val) > 1e-10:
                    vals.append(val)
            time.sleep_ms(200)
        return sorted(vals)[len(vals)//2] if vals else None

    def read(self):
        return {
            "level": self._get_reading(self.commands[0], "level"),
            "rs485_temperature": self._get_reading(self.commands[1], "rs485_temperature"),
            "ambient_temperature": self._get_reading(self.commands[2], "ambient_temperature")
        }


# --- 5. BUCLE PRINCIPAL Y START (Sin cambios) ---
async def _loop():
    """Bucle principal que coordina la lectura de todos los sensores."""
    rs485_reader = None
    try:
        i2c_bus = i2c()
        info("Bus I2C para sensores inicializado.")

        # Instanciamos el lector HÍBRIDO actualizado
        analog_reader = HybridAnalogSensors(i2c_bus, gain_index_val=gain_index)

        if sensor_params.ENABLE_RS485:
            rs485_reader = RS485Sensor()
            info("Módulo RS485 HABILITADO.")
        else:
            info("Módulo RS485 DESHABILITADO por configuración.")

        info("Tarea de sensores iniciada. Intervalo de lectura: 15s")
    except Exception as e:
        error(f"Fallo crítico al inicializar sensores, la tarea no se ejecutará: {e}")
        return

    while True:
        analog_data = analog_reader.read()
        if analog_data:
            current_readings["analog"].update(analog_data)
            info(f"Lecturas Analógicas: {current_readings['analog']}")

        if rs485_reader:
            rs485_data = rs485_reader.read()
            if rs485_data:
                current_readings["rs485"].update(rs485_data)
                info(f"Lecturas RS485: {current_readings['rs485']}")
        
        await asyncio.sleep(15)

def start():
    """Inicia la tarea de lectura de sensores en segundo plano."""
    info("Lanzando tarea de control de sensores...")
    asyncio.create_task(_loop())
