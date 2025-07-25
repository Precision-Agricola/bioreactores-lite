# tests/t07_display_driver.py
from ui.display import init, write
import time, gc

init()
write(("Test Line 1",
       "Line 2 OK",
       "Line 3 OK",
       "Line 4 OK"))

print(">>> Revisa LCD: deben verse las 4 líneas de prueba.")
time.sleep(5)
print("PASS t07_display_driver (visión manual)")
gc.collect()
