# device/tasks/display_task.py

import uasyncio as asyncio
from time import time
from hw.relay_controller import controller as relays
from ui.display import init as lcd_init, write
from tasks.sensor_task import current_readings

start_timestamp = 0
current_page = 0
PAGE_COUNT = 2

def ljust_manual(s, width, fillchar=' '):
    ln = len(s)
    if ln >= width: return s
    return s + (fillchar * (width - ln))

def _format_val(val, precision=0, width=4):
    if val is None:
        return ljust_manual("---", width)
    s_val = "{:.{}f}".format(val, precision)
    return ljust_manual(s_val, width)

async def _loop():
    global current_page
    
    while True:
        if start_timestamp > 0:
            seconds_elapsed = time() - start_timestamp
            days = (seconds_elapsed // 86400) + 1
            day_line = f"Day {int(days)}"
        else:
            day_line = "RTC not set"

        pump_line = "Pump ON" if relays.pump_is_on() else "Pump OFF"
        
        line_3 = ""
        line_4 = ""

        if current_page == 0:
            ph_val = _format_val(current_readings["analog"].get("ph_value"), 1)
            oxi_val = _format_val(current_readings["analog"].get("do_mg_l"), 1)
            nh3_val = _format_val(current_readings["analog"].get("nh3_ppm"), 1)
            s2h_val = _format_val(current_readings["analog"].get("s2h_ppm"), 1)

            line_3 = f"PH:  {ph_val} DO: {oxi_val}"
            line_4 = f"NH3: {nh3_val} S2H: {s2h_val}"
            
        elif current_page == 1:

            level_val = _format_val(current_readings["rs485"].get("level"), 1, 5) # 1 decimal (ej: 19.4)
            rs485_t_val_c = current_readings["rs485"].get("rs485_temperature")
            amb_t_val_c = current_readings["rs485"].get("ambient_temperature")

            rs485_t_val = _format_val(rs485_t_val_c, 1, 5) # ej: "24.0 "
            amb_t_val = _format_val(amb_t_val_c, 1, 4)   # ej: "--- "

            line_3 = f"Level: {level_val} cm"
            line_4 = f"T.L.:{rs485_t_val} T.A.:{amb_t_val}"

        write((
            ljust_manual(day_line, 20),
            ljust_manual(pump_line, 20),
            ljust_manual(line_3, 20),
            ljust_manual(line_4, 20)
        ))
        
        current_page = (current_page + 1) % PAGE_COUNT
        await asyncio.sleep(3)

def start():
    lcd_init()
    asyncio.create_task(_loop())

def set_start_time(timestamp):
    global start_timestamp
    start_timestamp = timestamp
