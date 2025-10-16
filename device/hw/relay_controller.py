# device/hw/relay_controller.py

from utils.logger import info
from hw.relays import (
    compressor_a,
    compressor_b,
    pump_relay,
)

class RelayController:
    def __init__(self):
        self._comp_a = compressor_a
        self._comp_b = compressor_b
        self._pump   = pump_relay

        # Estado inicial
        self._comp_a.off()
        self._comp_b.off()
        self._pump.off()

        # Arranca con A activo (como antes)
        self.set_compressors(a_on=True)
        info("RelayController ready")

    def set_compressors(self, *, a_on: bool):
        if a_on:
            self._comp_a.on(); self._comp_b.off()
        else:
            self._comp_b.on(); self._comp_a.off()
        info("Compressors -> %s" % ("A" if a_on else "B"))

    def toggle_pump(self):
        self._pump.toggle()
        info("Pump %s" % ("ON" if self._pump.is_on() else "OFF"))

    def pump_is_on(self):
        return self._pump.is_on()

    def compressors_state(self):
        return "A" if self._comp_a.is_on() else "B"

controller = RelayController()
