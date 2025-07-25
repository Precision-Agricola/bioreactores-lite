# tests/t05_control_task.py
import uasyncio as asyncio
from machine import Pin
from config.runtime import AUTO_PUMP_INTERVAL_MIN, AUTO_PUMP_DURATION_MIN
from hw.relay_controller import controller
from tasks.control_task import start as ctl_start

# → acorta tiempos para test (1 min y 0.5 min)
AUTO_PUMP_INTERVAL_MIN[:] = [1]         # monkey‑patch if list/attr
AUTO_PUMP_DURATION_MIN[:] = [0.5]

# botón virtual en GPIO18 reemplaza al real
BTN = Pin(18, Pin.OUT, value=1)

async def fake_press():
    await asyncio.sleep(30)   # después de 30 s
    BTN.value(0); await asyncio.sleep_ms(80)  # debounced press
    BTN.value(1)

async def main():
    ctl_start()               # lanza botón+auto‑loop
    asyncio.create_task(fake_press())
    await asyncio.sleep(90)   # total ensayo ≈ 90 s

    if controller.pump_is_on():
        raise SystemExit("FAIL: pump quedó ON al final")
    print("PASS t05_control_task")

asyncio.run(main())
