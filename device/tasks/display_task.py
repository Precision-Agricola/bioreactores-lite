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
        left3 = f"Level: {level:.2f}m" if isinstance(level, (int, float)) else "Level: ---"

        # DERECHA: valores REALES desde 'eng'
        e = current_readings.get("eng", {})
        ph  = e.get("pH")
        o2  = e.get("O2_mgL")
        nh3 = e.get("NH3_ppm")
        h2s = e.get("H2S_ppm")

        def val(v, fmt):
            try:
                return fmt.format(v)
            except:
                return "---"

        right1 = f"pH:{val(ph,'{:.2f}')}"[:8]
        right2 = f"O2:{val(o2,'{:.1f}')}"[:8]
        right3 = f"NH3:{val(nh3,'{:.0f}')}"[:8]
        right4 = f"H2S:{val(h2s,'{:.0f}')}"[:8]

        def pack(left_text, right_text):
            L = (left_text or "")
            R = (right_text or "")
            max_left = _COLS - len(R) - 1
            if max_left < 0:
                R = R[-(_COLS - 1):]
                max_left = _COLS - len(R) - 1
            if len(L) > max_left:
                L = L[:max_left]
            spaces = max(1, _COLS - len(L) - len(R))
            return (L + (" " * spaces) + R)[:_COLS]

        line1 = pack(left1, right1)
        line2 = pack(left2, right2)
        line3 = pack(left3, right3)
        line4 = pack("",    right4)

        write((line1, line2, line3, line4))
        await asyncio.sleep(3)

def start():
    lcd_init()
    asyncio.create_task(_loop())

def set_start_time(timestamp):
    global start_timestamp
    start_timestamp = timestamp
