from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
import hmac
import hashlib
from django.conf import settings

from people.models import People, EntranceQR
from entrances.models import Entrance


class ScannerQRScanTests(TestCase):
    def setUp(self):
        self.scan_url = reverse("scanner.scan")
        self.person = People.objects.create(
            name="Test User",
            nrc="123456",
            father_name="Father Name",
            address="Test Address",
        )
        self.qr = EntranceQR.objects.create(people=self.person)

    def _generate_valid_token(self, people_uuid):
        secret = settings.SECRET_KEY.encode("utf-8")
        signature = hmac.new(secret, str(people_uuid).encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{people_uuid}.{signature}"

    def test_successful_scan_creates_entrance(self):
        token = self._generate_valid_token(self.person.id)
        response = self.client.post(
            self.scan_url,
            data={"qr_data": token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertTrue(Entrance.objects.filter(people=self.person).exists())

    def test_duplicate_scan_returns_denied(self):
        token = self._generate_valid_token(self.person.id)
        self.client.post(
            self.scan_url,
            data={"qr_data": token},
            content_type="application/json",
        )
        response = self.client.post(
            self.scan_url,
            data={"qr_data": token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["status"], "denied")
        self.assertEqual(Entrance.objects.filter(people=self.person).count(), 1)

    def test_invalid_signature_returns_denied(self):
        response = self.client.post(
            self.scan_url,
            data={"qr_data": "invalid-token"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "denied")

    def test_missing_qr_data_returns_error(self):
        response = self.client.post(
            self.scan_url,
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    @patch("scanner.views.send_to_arduino", return_value=False)
    def test_arduino_write_failure_does_not_block_response(self, mock_send):
        token = self._generate_valid_token(self.person.id)
        response = self.client.post(
            self.scan_url,
            data={"qr_data": token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        mock_send.assert_called()

    @patch("scanner.views.send_to_arduino", return_value=False)
    def test_arduino_write_failure_on_duplicate_does_not_block_response(self, mock_send):
        token = self._generate_valid_token(self.person.id)
        self.client.post(
            self.scan_url,
            data={"qr_data": token},
            content_type="application/json",
        )
        response = self.client.post(
            self.scan_url,
            data={"qr_data": token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["status"], "denied")
        self.assertEqual(mock_send.call_count, 2)
