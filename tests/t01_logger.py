# test/t01_logger.py

import os, gc
from utils.logger import info, warning, error, _LOG_FILE

def fsize():
    try:
        return os.stat(_LOG_FILE)[6]
    except OSError:
        return 0

print("[t01] Logger rotation…")
start = fsize()

for _ in range(400):
    error("X"*16)

mid = fsize()

if mid <= start:
    raise SystemExit("FAIL: no escribió")
if mid > 200*1024:
    raise SystemExit("FAIL: no recortó a 200 kB máx")

info("LED OFF test")
warning("LED ON  test")
error("LED BLK test")

print("PASS t01_logger")
gc.collect()
