# tests/t06_flow_meter.py
import uasyncio as asyncio, time, gc
from machine import Pin, PWM
from config.pins import FLOW_SENSOR_PIN
from sensors.flow_meter import FlowMeter

FLOW_GEN_PIN = 27     # pin libre para generar pulsos
PWM_FREQ_HZ = 22      # ≈ 2 L/min para YF‑B1 -> 22 Hz según fórmula

fm = FlowMeter("YF-B1")     # factor (F+3)/11

async def generate_pulses(seconds=5):
    pwm = PWM(Pin(FLOW_GEN_PIN), freq=PWM_FREQ_HZ, duty=512)
    await asyncio.sleep(seconds)
    pwm.deinit()

async def main():
    asyncio.create_task(generate_pulses())
    await asyncio.sleep(5)
    lpm = fm.litres_per_min(5)
    print("Measured:", lpm, "L/min")
    if not 1.5 < lpm < 2.5:
        raise SystemExit("FAIL flow out of range")
    print("PASS t06_flow_meter")
    gc.collect()

asyncio.run(main())
