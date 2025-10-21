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
    """Implementación manual de ljust para MicroPython."""
    ln = len(s)
    if ln >= width:
        return s
    return s + (fillchar * (width - ln))

def _format_val(val, precision=0):
    """Función helper para formatear valores o mostrar '---'."""
    if val is None:
        return ljust_manual("---", 4)
    
    s_val = ""
    if precision == 0:
        s_val = str(int(val))
    else:
        s_val = "{:.{}f}".format(val, precision)
    
    return ljust_manual(s_val, 4)


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

            ph_val = _format_val(current_readings["analog"].get("ph"))
            oxi_val = _format_val(current_readings["analog"].get("oxigeno"))
            nh3_val = _format_val(current_readings["analog"].get("nh3_ppm"), 1) # 1 decimal
            s2h_val = _format_val(current_readings["analog"].get("s2h_ppm"), 1) # 1 decimal

            line_3 = f"PH:  {ph_val} Oxi: {oxi_val}"
            line_4 = f"NH3: {nh3_val} S2H: {s2h_val}"
            
        elif current_page == 1:

            level_val = _format_val(current_readings["rs485"].get("level"), 2)
            rs485_t_val = _format_val(current_readings["rs485"].get("rs485_temperature"), 1)
            amb_t_val = _format_val(current_readings["rs485"].get("ambient_temperature"), 1)

            line_3 = f"Level: {level_val} m"
            line_4 = f"T(RS): {rs485_t_val} T(A): {amb_t_val}"

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
