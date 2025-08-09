# /tests/system_check.py
import gc, time, machine

# Config & HW
from config.pins import i2c, SCL_PIN, SDA_PIN, BUTTON_PIN
from utils.drivers.ds3231 import DS3231
from hw.relay_controller import controller as relays
from ui.display import init as lcd_init, write as lcd_write


try:
    from config.system_version import VERSION, COMMIT, BUILD_DATE
except Exception:
    VERSION, COMMIT, BUILD_DATE = "dev", "local", "n/a"

# Opciones
FAST = True      # reduce tiempos de espera
DRY_RUN = False  # si True, no conmuta relés (solo verifica acceso)

# Helpers de salida
def ok(msg): print(f"✅ {msg}")
def warn(msg): print(f"⚠️  {msg}")
def fail(msg): print(f"❌ {msg}")

def line(title):
    print("\n" + "=" * 35)
    print(" " + title)
    print("=" * 35)

def check_env():
    line("Pre-Check")
    gc.collect()
    ok(f"Memoria libre inicial: {gc.mem_free()} bytes")
    ok(f"Version: {VERSION} ({COMMIT}) - Build: {BUILD_DATE} UTC")

def check_i2c():
    line("I2C")
    print(" Conexiones:")
    print(f"   SCL -> GPIO{SCL_PIN}")
    print(f"   SDA -> GPIO{SDA_PIN}\n")
    try:
        bus = i2c()
        devs = bus.scan()
        if not devs:
            warn("No se detectaron dispositivos en I2C.")
        else:
            ok(f"{len(devs)} dispositivo(s) encontrado(s): {[hex(d) for d in devs]}")
        return devs
    except Exception as e:
        fail(f"Error I2C: {e}")
        return []

def check_rtc():
    line("RTC (DS3231)")
    try:
        bus = i2c()
        if 0x68 not in bus.scan():
            warn("RTC 0x68 no detectado. Saltando prueba de RTC.")
            return
        ds = DS3231(bus)
        dt_ds = ds.datetime()
        machine.RTC().datetime(dt_ds)  # sync opcional
        ok(f"Hora DS3231: {dt_ds}")
        ok(f"Hora ESP32 : {time.localtime()}")
    except Exception as e:
        fail(f"Error RTC: {e}")

def check_lcd():
    line("LCD")
    try:
        lcd_init()
        lcd_write(("System Check", "LCD OK", "I2C Online", time.strftime("%H:%M:%S", time.localtime())))
        ok("LCD inicializado y escritura correcta.")
    except Exception as e:
        warn(f"LCD no disponible o error al escribir: {e}")

def check_relays():
    line("Relés (Bomba / Compresores)")
    wait_s = 1 if FAST else 2
    # Guardar estado inicial
    initial_pump = relays.pump_is_on()
    try:
        if DRY_RUN:
            warn("DRY_RUN activo: no se conmutan relés.")
            return

        # Bomba: toggle breve y restaurar
        relays.toggle_pump()
        time.sleep(wait_s)
        relays.toggle_pump()
        time.sleep(0.2)
        ok("Bomba conmutó correctamente (toggle ON/OFF).")

        # Compresores: A ON -> B ON -> ambos OFF
        relays.set_compressors(a_on=True)
        time.sleep(wait_s)
        relays.set_compressors(a_on=False)
        time.sleep(wait_s)
        relays.set_compressors(a_on=False)  # ambos OFF
        ok("Compresores conmutaron (A/B) y se restauraron a OFF.")

    except Exception as e:
        fail(f"Error en relés: {e}")
    finally:
        # Restauración: bomba al estado original, compresores OFF
        if relays.pump_is_on() != initial_pump:
            relays.toggle_pump()
        relays.set_compressors(a_on=False)

def check_button():
    line("Botón (lectura rápida)")
    try:
        pin = machine.Pin(BUTTON_PIN, machine.Pin.IN)
        t_end = time.ticks_add(time.ticks_ms(), 3000 if FAST else 5000)
        last = pin.value()
        pressed = False
        while time.ticks_diff(t_end, time.ticks_ms()) > 0:
            v = pin.value()
            if v != last:
                pressed = True
                break
            time.sleep_ms(50)
        if pressed:
            ok("Se detectó cambio de estado en el botón.")
        else:
            warn("Sin cambio detectado (posible: no pulsado / wiring).")
    except Exception as e:
        warn(f"No se pudo leer botón: {e}")

def check_persistence():
    line("Persistencia mínima")
    path = "start_time.txt"
    try:
        with open(path, "r") as f:
            content = f.read().strip()
        ok(f"Lectura {path}: '{content}'")
    except OSError:
        warn(f"No existe {path} (se crea en primer arranque por main).")
    except Exception as e:
        fail(f"Error accediendo {path}: {e}")

def check_memory():
    line("Memoria y GC")
    gc.collect()
    free = gc.mem_free()
    ok(f"Memoria libre tras pruebas: {free} bytes")
    if free < 120_000:
        warn("Memoria libre baja (<120KB). Revisa módulos cargados.")

def run():
    start_warns = 0
    start_fails = 0

    try:
        check_env()
        devs = check_i2c()
        check_rtc()
        check_lcd()
        check_relays()
        check_button()
        check_persistence()
        check_memory()
        print("\nResumen:")
        print("  Revisa los mensajes ✅/⚠️/❌ arriba. Si hay ❌, atiéndelos primero.")
        print("=" * 35)
    except Exception as e:
        fail(f"Excepción no controlada en system_check: {e}")

# REPL:
# >>> import system_check
# >>> system_check.run()
