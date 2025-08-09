# /tests/rtc_set.py

from config.pins import i2c, SCL_PIN, SDA_PIN
from utils.drivers.ds3231 import DS3231
import machine, time

def run():
    print("=" * 35)
    print(" RTC Set – DS3231")
    print("=" * 35)
    print(" Conexiones:")
    print(f"    SCL -> GPIO{SCL_PIN}")
    print(f"    SDA -> GPIO{SDA_PIN}")
    print("    VCC -> 3.3V")
    print("    GND -> GND\n")

    # ── ️ EDITA AQUÍ LA FECHA/HORA ─────────────────────────────────
    # Formato esperado por DS3231 / machine.RTC():
    # (year, month, day, weekday, hour, minute, second, subsecond)
    # Nota: weekday puede ir 0–6 (usaremos 0); subseconds = 0

    YEAR   = 2025
    MONTH  = 8
    DAY    = 9
    HOUR   = 12
    MINUTE = 0
    SECOND = 0
    WEEKDAY = 0     # 0–6; se ignora en la práctica para la mayoría de usos
    SUBSEC  = 0
    # ────────────────────────────────────────────────────────────────

    try:
        bus = i2c()
        if 0x68 not in bus.scan():
            print("⚠️  RTC (0x68) no detectado en el bus I2C.")
            print("   > Verifica conexiones y alimentación.")
            return

        ds = DS3231(bus)
        dt = (YEAR, MONTH, DAY, WEEKDAY, HOUR, MINUTE, SECOND, SUBSEC)

        ds.datetime(dt)

        machine.RTC().datetime(ds.datetime())

        print("✅ RTC configurado:")
        print("   DS3231:", ds.datetime())
        print("   ESP32 :", time.localtime())
    except Exception as e:
        print(f"❌ Error configurando RTC: {e}")
        return

    print("=" * 35)

# REPL:
# >>> import rtc_set
# >>> rtc_set.run()
