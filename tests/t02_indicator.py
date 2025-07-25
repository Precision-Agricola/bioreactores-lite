from machine import Pin
from config.pins import INDICATOR_PIN
from hw.indicator import set_level, start
import uasyncio

async def main():
    start()
    set_level("INFO");    await uasyncio.sleep(0.3)
    if Pin(INDICATOR_PIN).value() != 0:
        raise SystemExit("LED INFO FAIL")

    set_level("WARNING"); await uasyncio.sleep(0.3)
    if Pin(INDICATOR_PIN).value() == 0:
        raise SystemExit("LED WARN FAIL")

    set_level("ERROR"); await uasyncio.sleep(0.6)
    set_level("INFO")
    print("PASS t02_indicator")

uasyncio.run(main())
