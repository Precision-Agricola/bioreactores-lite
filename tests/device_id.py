# /tests/device_id.py
import machine
import binascii

def run():
    print("=" * 35)
    print(" Device ID – ESP32")
    print("=" * 35)

    try:
        uid = machine.unique_id()  # bytes
        hex_id = binascii.hexlify(uid).decode().upper()
        print(" Identificador único (machine.unique_id):")
        print(f"   Bytes  : {list(uid)}")
        print(f"   HEX    : {hex_id}")
    except Exception as e:
        print(f"❌ Error obteniendo Device ID: {e}")
        return

    print("=" * 35)

# REPL:
# >>> import device_id
# >>> device_id.run()
