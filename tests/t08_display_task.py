# tests/t08_display_task.py
import uasyncio as asyncio, time, gc
from tasks.display_task import start as disp_start
from hw.relay_controller import controller

async def simulate():
    await asyncio.sleep(4)
    controller.toggle_pump()      # Pump ON
    await asyncio.sleep(4)
    controller.set_compressors(a_on=False)  # Cambia a CompB
    await asyncio.sleep(4)
    controller.toggle_pump()      # Pump OFF

async def main():
    disp_start()
    asyncio.create_task(simulate())
    await asyncio.sleep(14)       # tiempo total del script
    print(">>> Verifica LCD: Día 1, líneas cambian conforme a eventos.")
    print("PASS t08_display_task (visión manual)")
    gc.collect()

asyncio.run(main())
