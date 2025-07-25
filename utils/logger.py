# utils/logger.py 

import os, time
from hw.indicator import set_level

_LOG_FILE         = "event.log"
_MAX_SIZE_BYTES   = 200 * 1024

_LEVELS = {
    "DEBUG":   10,
    "INFO":    20,
    "WARNING": 30,
    "ERROR":   40,
}

_current_level_num = _LEVELS["DEBUG"]

def set_level(level: str) -> None:
    """Change global log verbosity at runtime."""
    global _current_level_num
    lvl = level.upper()
    if lvl not in _LEVELS:
        raise ValueError("Logger: invalid level '%s'" % level)
    _current_level_num = _LEVELS[lvl]

def _timestamp() -> str:
    try:
        y, m, d, _, hh, mm, ss, _ = time.localtime()
        return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"
    except Exception:
        return f"t+{time.ticks_ms()}ms"

def _shrink_log() -> None:
    try:
        if os.stat(_LOG_FILE)[6] <= _MAX_SIZE_BYTES:
            return
        with open(_LOG_FILE, "rb") as f:
            data = f.read()
        keep = data[-_MAX_SIZE_BYTES // 2 :]
        with open(_LOG_FILE, "wb") as f:
            f.write(keep)
    except OSError:
        pass

def _write(line: str) -> None:
    try:
        with open(_LOG_FILE, "a") as f:
            f.write(line)
    except Exception as exc:
        print("LOG‑ERR:", exc, line, end="")

def log(level: str, msg: str) -> None:
    lvl_name = level.upper()
    lvl_num  = _LEVELS.get(lvl_name, 20)

    if lvl_num < _current_level_num:
        return

    record = f"[{_timestamp()}][{lvl_name}] {msg}\n"
    _write(record)
    _shrink_log()

    if lvl_name in ("INFO", "WARNING", "ERROR"):
        set_level(lvl_name)

def debug(msg: str)   -> None: log("DEBUG",   msg)
def info(msg: str)    -> None: log("INFO",    msg)
def warning(msg: str) -> None: log("WARNING", msg)
def error(msg: str)   -> None: log("ERROR",   msg)
