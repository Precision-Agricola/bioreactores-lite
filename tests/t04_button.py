from machine import Pin
from hw.button import Button
from hw.relay_controller import controller
import uasyncio

btn = Button()
test_pin = Pin(18, Pin.OUT, value=1)  # reconfig temporal

async def stim():
    await uasyncio.sleep_ms(50)
    test_pin.value(0); await uasyncio.sleep_ms(100)
    test_pin.value(1)

async def main():
    t = uasyncio.create_task(btn.run())
    await stim()
    await uasyncio.sleep_ms(100)
    if not controller.pump_is_on(): raise SystemExit("FAIL toggle")
    t.cancel(); print("PASS")

uasyncio.run(main())
