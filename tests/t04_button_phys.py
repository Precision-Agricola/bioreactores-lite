# tests/t04_button_phys

from hw.button import Button
from hw.relay_controller import controller
import uasyncio, gc

async def main():
    btn = Button()                           # usa GPIO18 como entrada
    uasyncio.create_task(btn.run())

    print("Pulsa el botón físico 2‑3 veces (20 s para la prueba)...")
    await uasyncio.sleep(20)

    # Apagamos bomba si quedó encendida
    if controller.pump_is_on():
        controller.toggle_pump()

    print("PASS t04_button_phys  (si viste la bomba alternar)")
    gc.collect()

uasyncio.run(main())
