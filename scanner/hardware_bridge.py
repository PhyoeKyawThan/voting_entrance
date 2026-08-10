import json
import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

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

def init_arduino_serial():
    global _ACTIVE_DEVICE
    config = get_scanner_hardware_config()
    
    if _ACTIVE_DEVICE is not None and _ACTIVE_DEVICE.is_open:
        return _ACTIVE_DEVICE

    if not config.port or serial is None:
        print("Serial library not installed or port not configured.")
        return None

    try:
        print(f"Initializing persistent Arduino Serial port on {config.port}...")
        dev = serial.Serial()
        dev.port = config.port
        dev.baudrate = config.baudrate
        dev.timeout = config.timeout
        dev.dtr = False

        dev.open()
        _ACTIVE_DEVICE = dev
        print("Arduino Serial connected and ready.")
    except Exception as e:
        print(f"Error opening Arduino serial port on startup: {e}")
        _ACTIVE_DEVICE = None

    return _ACTIVE_DEVICE

def _is_device_physically_connected(device):
    if device is None or not device.is_open:
        return False

    try:
        from serial.tools import list_ports
        if not any(p.device == device.port for p in list_ports.comports()):
            return False
    except Exception:
        pass

    try:
        _ = device.in_waiting
        return True
    except Exception:
        return False


def get_arduino_status():
    global _ACTIVE_DEVICE

    if _ACTIVE_DEVICE is None:
        return {
            "connected": False,
            "port": get_scanner_hardware_config().port,
            "error": "not_initialized",
        }

    if not _is_device_physically_connected(_ACTIVE_DEVICE):
        _ACTIVE_DEVICE = None
        return {
            "connected": False,
            "port": get_scanner_hardware_config().port,
            "error": "device_error",
        }

    return {
        "connected": True,
        "port": _ACTIVE_DEVICE.port,
        "baudrate": _ACTIVE_DEVICE.baudrate,
    }


def send_to_arduino(name: str, status: str, message: str = "") -> bool:
    global _ACTIVE_DEVICE

    if _ACTIVE_DEVICE is None or not _ACTIVE_DEVICE.is_open:
        _ACTIVE_DEVICE = init_arduino_serial()

    if _ACTIVE_DEVICE is None:
        return False

    payload = {
        "name": name[:20],
        "status": status[:10],
        "message": message[:40],
    }
    line = json.dumps(payload, separators=(",", ":")) + "\n"

    try:
        _ACTIVE_DEVICE.write(line.encode("utf-8"))
        _ACTIVE_DEVICE.flush()
        return True
    except Exception as e:
        print(f"Serial Write Error: {e}")
        _ACTIVE_DEVICE = None 
        return False