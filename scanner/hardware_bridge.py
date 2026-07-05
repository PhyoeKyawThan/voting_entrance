import json
import os
import time
import sys
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
    if sys.platform.startswith("win"):
        default_port = "COM3" 
    else:
        default_port = "/dev/ttyACM0" 
    return ScannerHardwareConfig(
        port=os.getenv("SCANNER_SERIAL_PORT", default_port),
        baudrate=int(os.getenv("SCANNER_SERIAL_BAUDRATE", "9600")),
        timeout=float(os.getenv("SCANNER_SERIAL_TIMEOUT", "1.0")),
    )

_ACTIVE_DEVICE = None

def get_serial_device(config: ScannerHardwareConfig):
    global _ACTIVE_DEVICE
    if _ACTIVE_DEVICE is None or not _ACTIVE_DEVICE.is_open:
        if not config.port or serial is None:
            return None
        try:
            _ACTIVE_DEVICE = serial.Serial(config.port, config.baudrate, timeout=config.timeout)
            time.sleep(2) 
        except Exception as e:
            print(f"Error opening serial port: {e}")
            _ACTIVE_DEVICE = None
    return _ACTIVE_DEVICE

def send_to_arduino(name: str, status: str, message: str = "") -> bool:
    config = get_scanner_hardware_config()
    device = get_serial_device(config)
    
    if device is None:
        return False

    payload = {
        "name": name[:20],
        "status": status[:10],
        "message": message[:40],
    }
    line = json.dumps(payload, separators=(",", ":")) + "\n"

    try:
        device.write(line.encode("utf-8"))
        device.flush()
        return True
    except Exception as e:
        print(f"Serial Write Error: {e}")
        return False
