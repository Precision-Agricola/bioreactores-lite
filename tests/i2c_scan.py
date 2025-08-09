# tests/i2c_scan.py

from config.pins import i2c, SCL_PIN, SDA_PIN

def run():
    print("=" * 35)
    print(" I2C Scan")
    print("=" * 35)
    print(" Conexiones:")
    print(f"    SCL -> GPIO{SCL_PIN}")
    print(f"    SDA -> GPIO{SDA_PIN}\n")

    try:
        bus = i2c()
        devices = bus.scan()
    except Exception as e:
        print(f"❌ Error en I2C: {e}")
        return

    if not devices:
        print("⚠️  No se detectaron dispositivos.")
    else:
        print(f"✅ {len(devices)} dispositivo(s) encontrado(s):")
        for addr in devices:
            print(f"   - {hex(addr)}")
    print("=" * 35)

# REPL:
# >>> import i2c_scan
# >>> i2c_scan.run()
