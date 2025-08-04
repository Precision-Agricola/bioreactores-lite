# device/ui/display.py

from config.pins import i2c
from utils.drivers.machine_i2c_lcd import I2cLcd
from utils.logger import info, error

_ADDR = 0x27
_ROWS = 4
_COLS = 20

class _MockLcd:
    def backlight_on(self): pass
    def clear(self): pass
    def move_to(self, col, row): pass
    def putstr(self, text): pass

_lcd = None

def _initialize_lcd():
    global _lcd
    if _lcd is not None:
        return

    try:
        lcd_obj = I2cLcd(i2c(), _ADDR, _ROWS, _COLS)
        info("Pantalla LCD encontrada y conectada en el bus I2C.")
        _lcd = lcd_obj
    except OSError:
        error("Dispositivo LCD no encontrado. El sistema continuará sin pantalla.")
        _lcd = _MockLcd()


def init():
    _initialize_lcd()
    _lcd.backlight_on()
    _lcd.clear()

def write(lines):
    _initialize_lcd()
    for row in range(_ROWS):
        _lcd.move_to(0, row)
        txt = lines[row] if row < len(lines) else ""
        formatted_txt = str(txt) + ' ' * (_COLS - len(str(txt)))
        _lcd.putstr(formatted_txt[:_COLS])
