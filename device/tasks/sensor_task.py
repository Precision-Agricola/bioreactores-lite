# device/tasks/sensor_task.py

import uasyncio as asyncio
from machine import ADC, Pin, UART
import time
import struct
from utils.logger import info, error
from config import pins
from config import sensor_params

current_readings = {
    "analog": {
        "p32": None, "p33": None, "p02": None, "p04": None,
    },
    "rs485": {
        "level": None, "rs485_temperature": None, "ambient_temperature": None,
    }
}

class AnalogSensors:
    def __init__(self):
        try:
            self.adc_p32 = ADC(Pin(pins.ANALOG_PIN_1))
            self.adc_p33 = ADC(Pin(pins.ANALOG_PIN_2))
            self.adc_p02 = ADC(Pin(pins.ANALOG_PIN_3))
            self.adc_p04 = ADC(Pin(pins.ANALOG_PIN_4))
            
            self.adc_p32.atten(ADC.ATTN_11DB)
            self.adc_p33.atten(ADC.ATTN_11DB)
            self.adc_p02.atten(ADC.ATTN_11DB)
            self.adc_p04.atten(ADC.ATTN_11DB)
            info("Sensores analógicos inicializados.")
        except Exception as e:
            error(f"No se pudieron inicializar los ADC: {e}")
            raise

    def read(self):
        try:
            return {
                "p32": self.adc_p32.read(), "p33": self.adc_p33.read(),
                "p02": self.adc_p02.read(), "p04": self.adc_p04.read(),
            }
        except Exception as e:
            error(f"Error al leer sensores analógicos: {e}")
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

async def _loop():
    """Bucle principal que coordina la lectura de todos los sensores."""
    rs485_reader = None
    try:
        analog_reader = AnalogSensors()

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
