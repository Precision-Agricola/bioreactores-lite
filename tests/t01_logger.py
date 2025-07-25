import os, gc, time
from utils.logger import debug, info, warning, error, _LOG_FILE

def file_size():
    try: return os.stat(_LOG_FILE)[6]
    except OSError: return 0

print("[t01] Logger rotation…")
start = file_size()

for _ in range(1500):  # ≈ 25 kB de texto
    error("X"*16)

mid = file_size()
if mid <= start or mid > 200*1024:
    raise SystemExit("FAIL: rotación no actúa")

info("Test INFO")      # LED OFF
warning("Test WARN")   # LED ON
error("Test ERR")      # LED BLINK

print("PASS")
gc.collect()
