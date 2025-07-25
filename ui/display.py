# ui/display.py

from config.pins import i2c
from utils.drivers.machine_i2c_lcd import I2cLcd

_ADDR = 0x38        # PCF8574A con A0–A2 en LOW; cambia a 0x27 si es PCF8574
_ROWS = 4
_COLS = 20

_lcd = I2cLcd(i2c(), _ADDR, _ROWS, _COLS)

def init():
    _lcd.backlight_on()
    _lcd.clear()

def write(lines):
    for row in range(_ROWS):
        _lcd.move_to(0, row)
        txt = lines[row] if row < len(lines) else ""
        _lcd.putstr(txt.ljust(_COLS)[:_COLS])
