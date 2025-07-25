# tests/t06_flow_meter.py

import uasyncio as asyncio, gc
from machine import Pin, PWM, WDT
from config.pins import FLOW_SENSOR_PIN
from sensors.flow_meter import FlowMeter

FLOW_GEN_PIN = 27                # une GPIO27 → GPIO19 (sensor PIN)
PWM_FREQ_HZ  = 22                # ≈ 2 L/min para YF‑B1
TEST_SEC     = 3                 # 3 s de ventana
wdt = WDT(timeout=15000)         # 15 s margen

fm = FlowMeter("YF-B1")

async def generate():
    pwm = PWM(Pin(FLOW_GEN_PIN), freq=PWM_FREQ_HZ, duty=512)
    await asyncio.sleep(TEST_SEC + 1)    # un poco más largo
    pwm.deinit()

async def main():
    asyncio.create_task(generate())
    await asyncio.sleep(1)
    lpm = fm.litres_per_min(TEST_SEC)
    wdt.feed()
    print("Measured:", lpm, "L/min")
    if not 1.5 < lpm < 2.5:
        raise SystemExit("FAIL flow out of range")
    print("PASS t06_flow_meter")
    gc.collect()

asyncio.run(main())
