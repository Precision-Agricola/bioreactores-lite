# /sensors/analog_readings.py
# Lector ultra-ligero de 4 sensores (0–3.3V) para ESP32.
# Devuelve SOLO valores “relativos” ya procesados:
#   pH (float), O2_mgL (float), NH3_pct (float), H2S_pct (float)

from machine import ADC, Pin

# ---- Pines (desde config si existe) ----
try:
    from config.pins import PH_SENSOR_PIN, O2_SENSOR_PIN, NH3_SENSOR_PIN, H2S_SENSOR_PIN
    _PH_PIN, _O2_PIN, _NH3_PIN, _H2S_PIN = PH_SENSOR_PIN, O2_SENSOR_PIN, NH3_SENSOR_PIN, H2S_SENSOR_PIN
except Exception:
    _PH_PIN, _O2_PIN, _NH3_PIN, _H2S_PIN = 32, 33, 2, 4

# ---- Constantes ADC ----
_ADC_MAX = 4095
_VREF    = 3.3

# ---- ADCs cacheados (no crear objetos en cada lectura) ----
def _mk_adc(pin_no):
    adc = ADC(Pin(pin_no))
    adc.atten(ADC.ATTN_11DB)      # 0–3.3V
    adc.width(ADC.WIDTH_12BIT)    # 12 bits
    return adc

_ADC_PH   = _mk_adc(_PH_PIN)
_ADC_O2   = _mk_adc(_O2_PIN)
_ADC_NH3  = _mk_adc(_NH3_PIN)
_ADC_H2S  = _mk_adc(_H2S_PIN)

def _v(adc):
    # lectura -> voltaje (redondeo corto para menos GC)
    raw = adc.read()
    return round((raw / _ADC_MAX) * _VREF, 3)

# ---- Calibraciones compactas (ajusta a tus datos) ----
def _ph_from_v(v):             # pH = m*V + b
    m, b = 3.9769, -1.8758
    ph = m * v + b
    if ph < 0: ph = 0
    if ph > 14: ph = 14
    return round(ph, 2)

def _o2_from_v(v):             # ~ lineal: 3.0V ≈ 20 mg/L @25°C
    mgL = (v / 3.0) * 20.0
    if mgL < 0: mgL = 0
    return round(mgL, 2)

def _pct_from_v(v):            # relativo 0–100 %
    pct = (v / _VREF) * 100.0
    if pct < 0: pct = 0
    if pct > 100: pct = 100
    return round(pct, 1)

# === API mínima para el resto del sistema ===
def read_relatives():
    """
    Devuelve dict plano y compacto:
      {'pH': 5.48, 'O2_mgL': 8.46, 'NH3_pct': 2.4, 'H2S_pct': 6.4}
    """
    v_ph  = _v(_ADC_PH)
    v_o2  = _v(_ADC_O2)
    v_nh3 = _v(_ADC_NH3)
    v_h2s = _v(_ADC_H2S)

    return {
        'pH':      _ph_from_v(v_ph),
        'O2_mgL':  _o2_from_v(v_o2),
        'NH3_pct': _pct_from_v(v_nh3),
        'H2S_pct': _pct_from_v(v_h2s),
    }
