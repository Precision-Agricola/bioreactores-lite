# device/tasks/sensor_task.py
#
# Lee sensores analógicos y RS485 en la misma tarea
# + Calcula valores “ingenierizados” (reales) a partir de ADC:
#   - pH (unid. pH)
#   - O2 (mg/L)
#   - NH3 (ppm)
#   - H2S (ppm)
#   - Nivel (m)
#   - Temperaturas (°C)
#
# Este módulo reemplaza completamente al anterior y unifica ambas lecturas.

import uasyncio as asyncio
from machine import ADC, Pin, UART
import time
import struct
from utils.logger import info, error
from config import pins, sensor_params


# =========================
#  Calibraciones (EDITABLE)
# =========================

# ADC → Voltios
ADC_MAX        = 4095
ADC_VREF       = 3.30
ADC_ATTEN_GAIN = 1.00

def adc_to_volts(raw):
    if raw is None:
        return None
    try:
        return (float(raw) / ADC_MAX) * ADC_VREF * ADC_ATTEN_GAIN
    except Exception:
        return None

# pH = m*V + b
PH_SLOPE   = 3.9769
PH_OFFSET  = -1.8758

# O2 mg/L (lineal)
DO_V_MIN      = 0.20
DO_V_MAX      = 3.00
DO_MG_L_MAX   = 20.0

# NH3 ppm
NH3_V_MIN     = 0.20
NH3_V_MAX     = 3.00
NH3_PPM_MAX   = 100.0

# H2S ppm
H2S_V_MIN     = 0.20
H2S_V_MAX     = 3.00
H2S_PPM_MAX   = 50.0


# =========================
#  Lecturas globales
# =========================

current_readings = {
    "analog": {
        "p32": None, "p33": None, "p02": None, "p04": None,
    },
    "rs485": {
        "level": None,
        "rs485_temperature": None,
        "ambient_temperature": None,
        # "status": "OK" / "NO_RESP"  # (opcional, si lo quieres usar)
    },
    "eng": {
        "pH": None, "O2_mgL": None, "NH3_ppm": None, "H2S_ppm": None,
        "pH_V": None, "O2_V": None, "NH3_V": None, "H2S_V": None,
    }
}


# =========================
#  Funciones auxiliares
# =========================

def clamp(x, lo, hi):
    try:
        return max(lo, min(hi, x))
    except Exception:
        return None

def map_linear(v, in_min, in_max, out_min, out_max):
    if v is None or in_max <= in_min:
        return None
    if v <= in_min:
        return out_min
    if v >= in_max:
        return out_max
    ratio = (v - in_min) / (in_max - in_min)
    return out_min + ratio * (out_max - out_min)


# =========================
#  Inicialización de sensores
# =========================

def init_analog():
    try:
        adc_p32 = ADC(Pin(pins.ANALOG_PIN_1))
        adc_p33 = ADC(Pin(pins.ANALOG_PIN_2))
        adc_p02 = ADC(Pin(pins.ANALOG_PIN_3))
        adc_p04 = ADC(Pin(pins.ANALOG_PIN_4))
        for adc in [adc_p32, adc_p33, adc_p02, adc_p04]:
            adc.atten(ADC.ATTN_11DB)
        info("Sensores analógicos inicializados.")
        return adc_p32, adc_p33, adc_p02, adc_p04
    except Exception as e:
        error(f"No se pudieron inicializar los ADC: {e}")
        raise


def init_rs485():
    try:
        Pin(sensor_params.RS485_RX, Pin.IN, Pin.PULL_UP)
        uart = UART(
            2,
            baudrate=9600,
            tx=sensor_params.RS485_TX,
            rx=sensor_params.RS485_RX,
            timeout=200,        # ms para read()
            timeout_char=20     # ms entre caracteres
        )
        de_re = Pin(sensor_params.RS485_DE_RE, Pin.OUT)
        de_re.off()  # recepción por defecto
        info("Sensor RS485 inicializado (UART2 @9600/8N1, timeouts).")
        return uart, de_re
    except Exception as e:
        error(f"No se pudo inicializar RS485: {e}")
        return None, None


# =========================
#  Comunicación RS485
# =========================

RS485_COMMANDS = [
    b'\x01\x03\x04\x0a\x00\x02\xE5\x39',  # nivel
    b'\x01\x03\x04\x08\x00\x02\x44\xF9',  # temp interna
    b'\x01\x03\x04\x0c\x00\x02\x05\x38'   # temp ambiente
]

def send_rs485(uart, de_re, cmd, rx_window_ms=800, idle_gap_ms=60, max_bytes=64, retries=3):
    """
    Envía 'cmd' y recibe respuesta con ventana y gap de inactividad.
    Reintenta 'retries' veces variando pequeños tiempos.
    Devuelve bytes o None.
    """
    for attempt in range(retries):
        try:
            # Limpia buffer previo
            try:
                _ = uart.read()
            except:
                pass

            # TX
            de_re.on()                          # habilita TX
            time.sleep_ms(1 + 2*attempt)        # pequeño jitter
            uart.write(cmd)
            time.sleep_ms(3 + 2*attempt)        # guarda silencio mínimo
            de_re.off()                         # RX

            # RX con ventana y gap
            start = time.ticks_ms()
            last_rx = start
            buf = b''

            while True:
                chunk = uart.read()
                if chunk:
                    buf += chunk
                    last_rx = time.ticks_ms()
                    if len(buf) >= max_bytes:
                        break
                else:
                    if time.ticks_diff(time.ticks_ms(), last_rx) >= idle_gap_ms:
                        break

                if time.ticks_diff(time.ticks_ms(), start) >= rx_window_ms:
                    break

                time.sleep_ms(5)

            if buf:
                return buf
        except Exception as e:
            error(f"RS485 intento {attempt+1} fallo: {e}")

    return None


def _to_hex(b):
    try:
        return ' '.join('{:02X}'.format(x) for x in b) if b else 'None'
    except:
        return str(b)

def decode_rs485(resp):
    """Intenta varios parseos y loguea la trama en HEX para diagnóstico."""
    if not resp:
        info("RS485 decode: respuesta vacía/None")
        return None

    hexs = _to_hex(resp)
    info("RS485 RESP HEX: " + hexs)

    # Esperado clásico: 01 03 04 [4 bytes de dato] CRC...
    try:
        if len(resp) >= 7 and resp[0] == 0x01 and resp[1] == 0x03 and resp[2] == 0x04:
            val_be = struct.unpack('>f', resp[3:7])[0]
            if abs(val_be) > 1e-10:
                return val_be
    except Exception as e:
        error(f"RS485 parse float BE falló: {e}")

    # Plan B: float LE en 3:7
    try:
        if len(resp) >= 7:
            val_le = struct.unpack('<f', resp[3:7])[0]
            if abs(val_le) > 1e-10:
                info("RS485 parse float LE usado")
                return val_le
    except Exception:
        pass

    # Plan C: entero 32 bits BE
    try:
        if len(resp) >= 7:
            u32_be = struct.unpack('>I', resp[3:7])[0]
            if u32_be != 0:
                info("RS485 parse u32 BE usado")
                return float(u32_be)
    except Exception:
        pass

    # Plan D: entero 16+16 (dos registros)
    try:
        if len(resp) >= 7:
            hi, lo = struct.unpack('>HH', resp[3:7])
            if hi != 0 or lo != 0:
                info(f"RS485 parse 2xU16 usado (hi={hi}, lo={lo})")
                # Heurística simple: nivel en metros como hi.lo/1000
                return float((hi << 16) | lo) / 1000.0
    except Exception:
        pass

    info("RS485 decode: no se pudo interpretar la respuesta")
    return None


# =========================
#  Tarea principal
# =========================

async def _loop():
    adc_p32, adc_p33, adc_p02, adc_p04 = init_analog()
    uart, de_re = (init_rs485() if sensor_params.ENABLE_RS485 else (None, None))

    while True:
        # --- Lectura analógica cruda ---
        try:
            raw = {
                "p32": adc_p32.read(),
                "p33": adc_p33.read(),
                "p02": adc_p02.read(),
                "p04": adc_p04.read(),
            }
            current_readings["analog"].update(raw)
        except Exception as e:
            error(f"Error lectura ADC: {e}")
            raw = None

        # --- Conversión a unidades reales ---
        if raw:
            v_ph  = adc_to_volts(raw["p32"])
            v_o2  = adc_to_volts(raw["p33"])
            v_nh3 = adc_to_volts(raw["p02"])
            v_h2s = adc_to_volts(raw["p04"])

            ph     = clamp(PH_SLOPE * v_ph + PH_OFFSET, 0.0, 14.0)
            o2_mgl = map_linear(v_o2, DO_V_MIN, DO_V_MAX, 0.0, DO_MG_L_MAX)
            nh3_ppm= map_linear(v_nh3, NH3_V_MIN, NH3_V_MAX, 0.0, NH3_PPM_MAX)
            h2s_ppm= map_linear(v_h2s, H2S_V_MIN, H2S_V_MAX, 0.0, H2S_PPM_MAX)

            current_readings["eng"].update({
                "pH": ph, "O2_mgL": o2_mgl, "NH3_ppm": nh3_ppm, "H2S_ppm": h2s_ppm,
                "pH_V": v_ph, "O2_V": v_o2, "NH3_V": v_nh3, "H2S_V": v_h2s,
            })

        # --- Lectura RS485 ---
        if uart and de_re:
            try:
                # Nivel
                raw = send_rs485(uart, de_re, RS485_COMMANDS[0])
                info("RS485 RAW (nivel): {}".format(raw))
                level = decode_rs485(raw)

                # Temperaturas
                temp_int = decode_rs485(send_rs485(uart, de_re, RS485_COMMANDS[1]))
                temp_amb = decode_rs485(send_rs485(uart, de_re, RS485_COMMANDS[2]))

                if isinstance(level, (int, float)):
                    current_readings["rs485"]["level"] = level
                    info("RS485 level = {:.2f} m".format(level))
                    # current_readings["rs485"]["status"] = "OK"  # opcional
                else:
                    info("RS485 level = ---")
                    # current_readings["rs485"]["status"] = "NO_RESP"  # opcional

                if isinstance(temp_int, (int, float)):
                    current_readings["rs485"]["rs485_temperature"] = temp_int
                if isinstance(temp_amb, (int, float)):
                    current_readings["rs485"]["ambient_temperature"] = temp_amb

                info(f"Lecturas RS485: {current_readings['rs485']}")
            except Exception as e:
                error(f"Error lectura RS485: {e}")

        # --- Log periódico ---
        info(f"Lecturas analógicas: {current_readings['eng']}")

        await asyncio.sleep(15)


def start():
    info("Iniciando tarea unificada de sensores (analógicos + RS485)...")
    asyncio.create_task(_loop())


# =========================
#  Helpers de diagnóstico (opcionales)
# =========================

def probe_rs485_once():
    """Dispara una lectura manual del nivel RS485 y retorna (raw_bytes, nivel_decodificado)."""
    try:
        uart, de_re = init_rs485()
        raw = send_rs485(uart, de_re, RS485_COMMANDS[0])
        lvl = decode_rs485(raw)
        info("PROBE RS485 RAW: {}".format(raw))
        info("PROBE RS485 level: {}".format(lvl))
        return raw, lvl
    except Exception as e:
        error("PROBE RS485 failed: {}".format(e))
        return None, None


def _crc16_modbus(data):
    crc = 0xFFFF
    for ch in data:
        crc ^= ch
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def _build_fc3(addr, reg, qty):
    # addr: slave id (1..247), reg: start address, qty: number of regs
    pdu = bytes([addr, 0x03, (reg>>8)&0xFF, reg&0xFF, (qty>>8)&0xFF, qty&0xFF])
    crc = _crc16_modbus(pdu)
    return pdu + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

def probe_rs485_scan_basic(addr_list=(1,), regs=(0x0000,0x0001,0x0002,0x0040,0x0400,0x0408,0x040A,0x040C), qty=2):
    """
    Intenta lecturas FC3 (qty=2) en direcciones comunes de holding regs.
    Devuelve { (addr,reg): (raw_hex, valor_decodificado) } para respuestas no vacías.
    Úsalo desde REPL:
      from tasks import sensor_task
      sensor_task.probe_rs485_scan_basic(addr_list=(1,2), regs=(0x0000,0x0400,0x0408,0x040A,0x040C))
    """
    results = {}
    try:
        uart, de_re = init_rs485()
        for a in addr_list:
            for r in regs:
                cmd = _build_fc3(a, r, qty)
                raw = send_rs485(uart, de_re, cmd)
                if raw:
                    val = decode_rs485(raw)
                    results[(a, r)] = (_to_hex(raw), val)
                    info("SCAN a={} reg=0x{:04X} -> RAW:{} VAL:{}".format(a, r, results[(a, r)][0], val))
                else:
                    info("SCAN a={} reg=0x{:04X} -> sin respuesta".format(a, r))
                time.sleep_ms(150)
    except Exception as e:
        error("probe_rs485_scan_basic error: {}".format(e))
    return results


# =========================
#  Herramientas de SHELL (solo lectura)
#  - No envían nada por RS485.
#  - Puedes usarlas en REPL/Thonny.
# =========================

def show_rs485_snapshot():
    """
    Imprime y devuelve el diccionario RS485 actual.
    Solo lectura de memoria (no transmite).
    """
    try:
        d = dict(current_readings.get("rs485", {}))
    except Exception:
        d = {}
    print("[RS485]", d)
    return d


def show_logs_tail(path='event.log', max_lines=200):
    """
    Muestra las últimas 'max_lines' líneas del log.
    Solo lectura de archivo (no transmite).
    """
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        for line in lines[-max_lines:]:
            print(line, end='')
    except Exception as e:
        print("ERROR leyendo {}: {}".format(path, e))


import uasyncio as _asyncio  # alias local para evitar sombras

async def watch_rs485(period=2, print_empty=False):
    """
    Imprime RS485 cuando cambie o cada 'period' s si print_empty=True.
    Solo lectura (no transmite).
    """
    prev = None
    while True:
        try:
            d = dict(current_readings.get("rs485", {}))
        except Exception:
            d = {}
        if d != prev or print_empty:
            print("[RS485]", d)
            prev = d
        await _asyncio.sleep(period)


def start_watch_rs485(period=2, print_empty=False):
    """
    Lanza el watcher en background. Úsalo desde REPL:
      from tasks.sensor_task import start_watch_rs485
      start_watch_rs485(period=2)
    """
    try:
        _asyncio.create_task(watch_rs485(period=period, print_empty=print_empty))
        print("watch_rs485 iniciado (period={}s, print_empty={})".format(period, print_empty))
    except Exception as e:
        print("No se pudo iniciar watch_rs485:", e)
