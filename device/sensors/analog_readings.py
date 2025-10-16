# /sensors/analog_readings.py
# Lector de sensores analógicos (pH, O2, NH3, H2S)
# Devuelve: {'pH': x.xx, 'O2_pct': y.yy, 'NH3_ppm': z, 'H2S_ppm': w}

from machine import ADC, Pin

# --- Pines desde config ---
try:
    from config.pins import PH_SENSOR_PIN, O2_SENSOR_PIN, NH3_SENSOR_PIN, H2S_SENSOR_PIN
    _PH_PIN, _O2_PIN, _NH3_PIN, _H2S_PIN = PH_SENSOR_PIN, O2_SENSOR_PIN, NH3_SENSOR_PIN, H2S_SENSOR_PIN
except Exception:
    _PH_PIN, _O2_PIN, _NH3_PIN, _H2S_PIN = 32, 33, 2, 4

# --- Configuración ADC ---
_ADC_MAX = 4095
_VREF    = 3.3

def _mk_adc(pin_no):
    adc = ADC(Pin(pin_no))
    adc.atten(ADC.ATTN_11DB)   # rango completo 0–3.3V
    adc.width(ADC.WIDTH_12BIT)
    return adc

_ADC_PH   = _mk_adc(_PH_PIN)
_ADC_O2   = _mk_adc(_O2_PIN)
_ADC_NH3  = _mk_adc(_NH3_PIN)
_ADC_H2S  = _mk_adc(_H2S_PIN)

def _v(adc):
    return round((adc.read() / _ADC_MAX) * _VREF, 3)

# ---- Calibraciones ----
# Ajusta estas fórmulas según tus lecturas reales.

def _ph_from_v(v):
    # DFRobot Gravity pH V2
    m, b = 3.9769, -1.8758
    ph = m * v + b
    return round(max(0, min(ph, 14)), 2)

def _o2_from_v(v):
    # DFRobot DO SEN0237 - convertir a % saturación (0–100%)
    # 3.0 V ≈ 100% O2; 0 V ≈ 0%
    pct = (v / 3.0) * 100.0
    return round(max(0, min(pct, 100)), 1)

def _nh3_from_v(v):
    # Sensor MEMS NH3 (0–50 ppm ≈ 0–3.3V)
    ppm = (v / 3.3) * 50.0
    return round(max(0, ppm), 1)

def _h2s_from_v(v):
    # Sensor MEMS H2S (0–50 ppm ≈ 0–3.3V)
    ppm = (v / 3.3) * 50.0
    return round(max(0, ppm), 1)

# === API principal ===
def read_relatives():
    """
    Devuelve:
      {'pH': 5.48, 'O2_pct': 87.5, 'NH3_ppm': 3.2, 'H2S_ppm': 6.4}
    """
    v_ph  = _v(_ADC_PH)
    v_o2  = _v(_ADC_O2)
    v_nh3 = _v(_ADC_NH3)
    v_h2s = _v(_ADC_H2S)

    return {
        'pH':      _ph_from_v(v_ph),
        'O2_pct':  _o2_from_v(v_o2),
        'NH3_ppm': _nh3_from_v(v_nh3),
        'H2S_ppm': _h2s_from_v(v_h2s),
    }
