import logging
from django.core.management.base import BaseCommand
from scanner.hardware_bridge import get_arduino_status, init_arduino_serial

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reinitialize Arduino serial connection if it is offline."

    def handle(self, *args, **options):
        status = get_arduino_status()
        if status.get("connected"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Arduino already connected on {status.get('port')}"
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Arduino offline (error={status.get('error')}). Attempting reconnect..."
            )
        )

        device = init_arduino_serial()
        if device is None:
            logger.error("Failed to reconnect Arduino serial port.")
            self.stderr.write(
                self.style.ERROR("Arduino reconnection failed.")
            )
        else:
            logger.info("Arduino serial port reconnected successfully.")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Arduino reconnected on {device.port} at {device.baudrate} baud."
                )
            )
