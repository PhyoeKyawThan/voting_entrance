import hmac
import hashlib
from django.conf import settings 

def verify_qr_token(scanned_string):
    try:
        scanned_uid, scanned_sig = scanned_string.split('.')
        secret = settings.SECRET_KEY.encode('utf-8')
        expected_sig = hmac.new(secret, scanned_uid.encode('utf-8'), hashlib.sha256).hexdigest()
        if hmac.compare_digest(scanned_sig, expected_sig):
            return scanned_uid 
        return None
    except (ValueError, AttributeError):
        return None