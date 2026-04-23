import json
import os
from dataclasses import dataclass


try:
    import serial
except ImportError:  
    serial = None


@dataclass(frozen=True)
class ScannerHardwareConfig:
    port: str
    baudrate: int = 9600
    timeout: float = 1.0


def get_scanner_hardware_config() -> ScannerHardwareConfig:
    return ScannerHardwareConfig(
        port=os.getenv("SCANNER_SERIAL_PORT", ""),
        baudrate=int(os.getenv("SCANNER_SERIAL_BAUDRATE", "9600")),
        timeout=float(os.getenv("SCANNER_SERIAL_TIMEOUT", "1.0")),
    )


def send_to_arduino(name: str, status: str, message: str = "") -> bool:
    config = get_scanner_hardware_config()
    if not config.port or serial is None:
        return False

    payload = {
        "name": name[:20],
        "status": status[:10],
        "message": message[:40],
    }
    line = json.dumps(payload, separators=(",", ":")) + "\n"

    try:
        with serial.Serial(config.port, config.baudrate, timeout=config.timeout) as device:
            device.write(line.encode("utf-8"))
            device.flush()
        return True
    except Exception:
        return False
