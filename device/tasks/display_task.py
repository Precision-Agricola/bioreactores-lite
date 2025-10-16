# device/tasks/display_task.py

import uasyncio as asyncio
from time import time
from hw.relay_controller import controller as relays
from ui.display import init as lcd_init, write
from tasks.sensor_task import current_readings

_COLS = 20
start_timestamp = 0

async def _loop():
    while True:
        # Izquierda: Día de inoculación
        if start_timestamp > 0:
            seconds_elapsed = time() - start_timestamp
            days = int(seconds_elapsed // 86400) + 1
            left1 = f"Day {days}"
        else:
            left1 = "RTC not set"

        # Izquierda: estado de bomba
        left2 = "Pump ON" if relays.pump_is_on() else "Pump OFF"

        # Izquierda: nivel (RS485)
        level = current_readings.get("rs485", {}).get("level")
        left3 = f"Level: {level:.2f}m" if level is not None else "Level: ---"

        # ==== DERECHA: valores REALES desde 'eng' (sensor_task) ====
        e = current_readings.get("eng", {})
        ph   = e.get("pH")         # unidades pH
        o2   = e.get("O2_mgL")     # mg/L
        nh3  = e.get("NH3_ppm")    # ppm
        h2s  = e.get("H2S_ppm")    # ppm

        def val(v, fmt):
            try:
                return fmt.format(v)
            except:
                return "---"

        # Compactos para que quepan en el borde derecho (≤ 8 chars)
        right1 = f"pH:{val(ph,'{:.2f}')}"     # ej: pH:7.02
        right2 = f"O2:{val(o2,'{:.1f}')}"     # ej: O2:8.5
        right3 = f"NH3:{val(nh3,'{:.0f}')}"   # ej: NH3:12
        right4 = f"H2S:{val(h2s,'{:.0f}')}"   # ej: H2S:3

        right1 = right1[:8]
        right2 = right2[:8]
        right3 = right3[:8]
        right4 = right4[:8]

        # Ensamble simple: izquierda + espacios + derecha, total <= 20
        def pack(left_text, right_text):
            L = (left_text or "")
            R = (right_text or "")
            max_left = _COLS - len(R) - 1
            if max_left < 0:
                # Si por alguna razón R es largo, recortamos más
                R = R[-(_COLS - 1):]
                max_left = _COLS - len(R) - 1
            if len(L) > max_left:
                L = L[:max_left]
            spaces = _COLS - len(L) - len(R)
            if spaces < 1:
                spaces = 1
            return (L + (" " * spaces) + R)[:_COLS]

        line1 = pack(left1, right1)  # Day ...         pH:7.02
        line2 = pack(left2, right2)  # Pump ...        O2:8.5
        line3 = pack(left3, right3)  # Level ...       NH3:12
        line4 = pack("",    right4)  #                H2S:3

        write((line1, line2, line3, line4))
        await asyncio.sleep(3)

def start():
    lcd_init()
    asyncio.create_task(_loop())

def set_start_time(timestamp):
    global start_timestamp
    start_timestamp = timestamp
