# tests/t04_button_sim

from machine import Pin
from config.pins import BUTTON_PIN
from hw.button import Button
from hw.relay_controller import controller
import uasyncio, gc

btn = Button()
test_pin = Pin(BUTTON_PIN, Pin.OUT, value=1)       # reconfig temporal

async def stim():
    await uasyncio.sleep_ms(50)
    test_pin.value(0); await uasyncio.sleep_ms(80) # flanco ↓ simulado
    test_pin.value(1)

async def main():
    task = uasyncio.create_task(btn.run())
    await stim()
    await uasyncio.sleep_ms(120)
    assert controller.pump_is_on(), "FAIL toggle"
    controller.toggle_pump()       # ← apaga la bomba
    task.cancel()
    print("PASS t04_button_sim")
    gc.collect()

uasyncio.run(main())
