# device/tasks/sensor_task.py
#
# Lee sensores analógicos y RS485
# + Calcula valores “ingenierizados” (reales) a partir de ADC:
#   - pH (unid. pH)
#   - O2 (mg/L)
#   - NH3 (ppm)
#   - H2S (ppm)

import uasyncio as asyncio
from machine import ADC, Pin, UART
import time
import struct
from utils.logger import info, error
from config import pins
from config import sensor_params

# =========================
#  Calibraciones (EDITABLE)
# =========================

# ADC → Voltios
ADC_MAX        = 4095            # Resolución ADC ESP32 (12 bits)
ADC_VREF       = 3.30            # Vref efectiva (ajústala tras comparar con multímetro)
ADC_ATTEN_GAIN = 1.00            # Ganancia corregida por atenuación/escala real (11dB ~ 1.0–1.1)

def adc_to_volts(raw):
    if raw is None:
        return None
    try:
        return (float(raw) / ADC_MAX) * ADC_VREF * ADC_ATTEN_GAIN
    except Exception:
        return None

# pH = m*V + b  (usa tu última calibración real)
PH_SLOPE   = 3.9769
PH_OFFSET  = -1.8758

# DO mg/L (lineal por defecto: 0.20–3.00 V → 0–20 mg/L)
DO_V_MIN      = 0.20
DO_V_MAX      = 3.00
DO_MG_L_MAX   = 20.0

# NH3 ppm (lineal por defecto: 0.20–3.00 V → 0–100 ppm)
NH3_V_MIN     = 0.20
NH3_V_MAX     = 3.00
NH3_PPM_MAX   = 100.0

# H2S ppm (lineal por defecto: 0.20–3.00 V → 0–50 ppm)
H2S_V_MIN     = 0.20
H2S_V_MAX     = 3.00
H2S_PPM_MAX   = 50.0

def clamp(x, lo, hi):
    try:
        return max(lo, min(hi, x))
    except Exception:
        return None

def map_linear(v, in_min, in_max, out_min, out_max):
    """Mapeo lineal con saturación en extremos."""
    try:
        if v is None:
            return None
        if in_max <= in_min:
            return None
        if v <= in_min:
            return out_min
        if v >= in_max:
            return out_max
        ratio = (v - in_min) / (in_max - in_min)
        return out_min + ratio * (out_max - out_min)
    except Exception:
        return None

# =========================
#  Estructura de lecturas
# =========================

current_readings = {
    "analog": {          # crudo
        "p32": None, "p33": None, "p02": None, "p04": None,
    },
    "rs485": {           # reales (del sensor RS485)
        "level": None, "rs485_temperature": None, "ambient_temperature": None,
    },
    "eng": {             # INGENIERIZADO (reales calculados desde ADC)
        "pH": None,          # unidades pH
        "O2_mgL": None,      # mg/L
        "NH3_ppm": None,     # ppm
        "H2S_ppm": None,     # ppm
        # Para depuración, también guardamos voltajes calculados:
        "pH_V": None,
        "O2_V": None,
        "NH3_V": None,
        "H2S_V": None,
    }
}

# =========================
#   Clases de sensores
# =========================

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

    def read_raw(self):
        try:
            return {
                "p32": self.adc_p32.read(), "p33": self.adc_p33.read(),
                "p02": self.adc_p02.read(), "p04": self.adc_p04.read(),
            }
        except Exception as e:
            error(f"Error al leer sensores analógicos: {e}")
            return None

    def compute_engineered(self, raw):
        """Convierte crudo → voltios → unidades reales, usando las constantes de calibración."""
        try:
            # Voltajes
            v_ph  = adc_to_volts(raw.get("p32") if raw else None)
            v_o2  = adc_to_volts(raw.get("p33") if raw else None)
            v_nh3 = adc_to_volts(raw.get("p02") if raw else None)
            v_h2s = adc_to_volts(raw.get("p04") if raw else None)

            # pH
            ph = None
            if v_ph is not None:
                ph = clamp(PH_SLOPE * v_ph + PH_OFFSET, 0.0, 14.0)

            # O2 mg/L (lineal por defecto)
            o2_mgl = map_linear(v_o2, DO_V_MIN, DO_V_MAX, 0.0, DO_MG_L_MAX)

            # NH3 ppm (lineal por defecto)
            nh3_ppm = map_linear(v_nh3, NH3_V_MIN, NH3_V_MAX, 0.0, NH3_PPM_MAX)

            # H2S ppm (lineal por defecto)
            h2s_ppm = map_linear(v_h2s, H2S_V_MIN, H2S_V_MAX, 0.0, H2S_PPM_MAX)

            return {
                "pH": ph,
                "O2_mgL": o2_mgl,
                "NH3_ppm": nh3_ppm,
                "H2S_ppm": h2s_ppm,
                "pH_V": v_ph,
                "O2_V": v_o2,
                "NH3_V": v_nh3,
                "H2S_V": v_h2s,
            }
        except Exception as e:
            error(f"Error al convertir lecturas analógicas a unidades reales: {e}")
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

# =========================
#         Tarea
# =========================


        # Analógico crudo
        analog_data = analog_reader.read_raw()
        if analog_data:
            current_readings["analog"].update(analog_data)

            # Ingenierizado (reales)
            eng = analog_reader.compute_engineered(analog_data)
            if eng:
                current_readings["eng"].update(eng)

            info(f"Lecturas Analógicas (crudo): {current_readings['analog']}")
            info(f"Lecturas Analógicas (reales): {current_readings['eng']}")

        # RS485
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
