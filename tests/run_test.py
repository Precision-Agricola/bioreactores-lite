# run_tests.py

import uasyncio
from config.pins import i2c
from hw.relays import compressor_a, compressor_b, pump_relay
from hw.relay_controller import controller as relays
from sensors.flow_meter import FlowMeter

TECHNICIAN_DELAY_S = 5

def check(description, expected, actual):
    if expected == actual:
        print(f"  [PASS] {description}")
    else:
        print(f"  [FAIL] {description}")
        print(f"         -> Se esperaba: {expected}, pero el valor fue: {actual}")


def test_i2c_devices():

    print("\n--- PRUEBA 1: Verificación de Dispositivos I2C ---")
    EXPECTED_LCD_ADDR = 0x27
    EXPECTED_RTC_ADDR = 0x68
    try:
        found_devices = i2c().scan()
        found_hex = [hex(d) for d in found_devices]
        print(f"Dispositivos encontrados en el bus I2C: {found_hex}")
        check(f"La pantalla LCD (en {hex(EXPECTED_LCD_ADDR)}) debe ser detectada.",
              True, EXPECTED_LCD_ADDR in found_devices)
        check(f"El reloj RTC (en {hex(EXPECTED_RTC_ADDR)}) debe ser detectado.",
              True, EXPECTED_RTC_ADDR in found_devices)
    except Exception as e:
        print(f"  [FAIL] Ocurrió un error durante el escaneo I2C: {e}")


async def test_actuators_visual():

    print("\n--- PRUEBA 2: Acción del Botón Manual de la Bomba ---")
    if pump_relay.is_on(): relays.toggle_pump()
    print("--> OBSERVE: El relé de la BOMBA debe estar APAGADO.")
    check("Estado inicial de la bomba.", False, pump_relay.is_on())
    await uasyncio.sleep(TECHNICIAN_DELAY_S)
    print("\n--> ACCIÓN: Simulando 1ra pulsación... Observe el relé.")
    relays.toggle_pump()
    check("Después de la 1ra pulsación, la bomba debe estar ENCENDIDA.", True, pump_relay.is_on())
    await uasyncio.sleep(TECHNICIAN_DELAY_S)
    print("\n--> ACCIÓN: Simulando 2da pulsación... Observe el relé.")
    relays.toggle_pump()
    check("Después de la 2da pulsación, la bomba debe estar APAGADA.", False, pump_relay.is_on())
    await uasyncio.sleep(TECHNICIAN_DELAY_S)
    print("\n--- PRUEBA 3: Alternancia de Compresores ---")
    print("\n--> ACCIÓN: Activando Compresor A... Observe los relés.")
    relays.set_compressors(a_on=True)
    check("Compresor A debería estar ENCENDIDO.", True, compressor_a.is_on())
    check("Compresor B debería estar APAGADO.", False, compressor_b.is_on())
    await uasyncio.sleep(TECHNICIAN_DELAY_S)
    print("\n--> ACCIÓN: Activando Compresor B... Observe los relés.")
    relays.set_compressors(a_on=False)
    check("Compresor A debería estar APAGADO.", False, compressor_a.is_on())
    check("Compresor B debería estar ENCENDIDO.", True, compressor_b.is_on())
    await uasyncio.sleep(TECHNICIAN_DELAY_S)
    print("\n--> Finalizando prueba. Dejando Compresor A encendido.")
    relays.set_compressors(a_on=True)

async def test_flow_sensor_task():
    """Verifica que la tarea del software del sensor de flujo se ejecuta."""
    print("\n--- PRUEBA 4: Tarea del Sensor de Flujo ---")
    print("--> Verificando que el software de monitoreo de flujo se inicia...")
    
    test_state = {'callback_fired': False}

    def flow_callback(lpm):
        print(f"  (Callback de flujo ejecutado. Lectura: {lpm:.2f} L/min)")
        test_state['callback_fired'] = True

    flow_meter = FlowMeter()
    uasyncio.create_task(flow_meter.task(interval_s=3, cb=flow_callback))
    
    print(f"--> Esperando {TECHNICIAN_DELAY_S} segundos para recibir una lectura (aunque sea 0.0 L/min)...")
    await uasyncio.sleep(TECHNICIAN_DELAY_S)
    
    check("El software del sensor de flujo está activo y funcionando.", True, test_state['callback_fired'])


async def run_technician_test_suite():
    """Ejecuta todas las pruebas para el técnico de forma secuencial."""
    print("\n" + "="*50)
    print("  MODO DE PRUEBA PARA TÉCNICO (Observación Visual)")
    print(f"  (Habrá una pausa de {TECHNICIAN_DELAY_S} segundos entre cada paso)")
    print("="*50)

    test_i2c_devices()
    await test_actuators_visual()
    await test_flow_sensor_task()

    print("\n" + "="*50)
    print("        FIN DE LA PRUEBA PARA TÉCNICO")
    print("="*50 + "\n")


if __name__ == '__main__':
    print("Iniciando secuencia de pruebas guiadas...")
    print("Asegúrese de que el sistema esté en modo PROGRAM (ambos switches en OFF).")
    
    try:
        uasyncio.run(run_technician_test_suite())
    except KeyboardInterrupt:
        print("\nPruebas detenidas por el usuario.")
    except Exception as e:
        print(f"\nHa ocurrido un error inesperado durante las pruebas: {e}")
