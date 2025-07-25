# tests/t03_relays

from hw.relay_controller import controller
print("Inicial:", controller.compressors_state())  # "A"
controller.set_compressors(a_on=False)
print("Ahora  :", controller.compressors_state())  # "B"
controller.toggle_pump()
print("Pump ON?", controller.pump_is_on())
controller.toggle_pump() 
print("PASS t03_relays")