from hw.relay_controller import controller
print("[t03] Complementary compressors…")
controller.set_compressors(a_on=True)
if not controller.compressors_state() == "A": raise SystemExit("FAIL A")
controller.set_compressors(a_on=False)
if not controller.compressors_state() == "B": raise SystemExit("FAIL B")
controller.toggle_pump(); controller.toggle_pump()  # ON→OFF
print("PASS")
