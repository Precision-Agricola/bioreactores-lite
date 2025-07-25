# tests/t05_control_task.py   (versión final)

import uasyncio as asyncio
from machine import Pin, WDT
import config.runtime as rt
from config.pins import BUTTON_PIN
from hw.relay_controller import controller

rt.AUTO_PUMP_INTERVAL_MIN = 1
rt.AUTO_PUMP_DURATION_MIN = 0.5

from tasks.control_task import start as ctl_start

BTN = Pin(BUTTON_PIN, Pin.OUT, value=1)
wdt = WDT(timeout=120000)

async def fake_press():
    await asyncio.sleep(30)
    BTN.value(0); await asyncio.sleep_ms(80)
    BTN.value(1)

async def main():
    ctl_start()
    asyncio.create_task(fake_press())

    for _ in range(90):
        wdt.feed()
        await asyncio.sleep(1)

    if controller.pump_is_on():
        raise SystemExit("FAIL: pump quedó ON al final")

    print("PASS t05_control_task")

asyncio.run(main())
