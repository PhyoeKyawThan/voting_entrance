from django.db import models
import uuid
import hmac
import hashlib
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings 
from datetime import datetime

def upload_to_unique(instance, filename):
    ext = filename.split('.')[-1]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"profiles/{instance.student_number}_{timestamp}.{ext}"


class Student(models.Model):
    
    student_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    student_number = models.IntegerField(null=False)
    name = models.CharField(max_length=50)
    picture = models.ImageField(
        upload_to=upload_to_unique,
        blank=True,
        null=True
    )
    roll_no = models.CharField(max_length=10)
    current_semester = models.IntegerField()
    nrc = models.CharField(max_length=100)
    father_name = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    birth_date = models.DateTimeField()

    register_date = models.DateTimeField(auto_now_add=True)

    def is_new_student(self):
        return self.current_semester == 1

    def __str__(self):
        return f"name - {self.name}, roll_no - {self.roll_no}"

class EntranceQR(models.Model):
    student = models.ForeignKey(
        'Student', 
        on_delete=models.CASCADE, 
        related_name='qr_codes'
    )
    qr_code_data = models.CharField(max_length=500, unique=True, editable=False)
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def generate_signature(self, data):
        secret = settings.SECRET_KEY.encode('utf-8')
        message = str(data).encode('utf-8')
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    def save(self, *args, **kwargs):
        if not self.qr_code_data:
            uid = str(self.student.student_id)
            signature = self.generate_signature(uid)
            self.qr_code_data = f"{uid}.{signature}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.qr_code_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        file_name = f"qr-{self.student.roll_no}-{uuid.uuid4().hex[:6]}.png"
        self.qr_image.save(file_name, File(buffer), save=False)
        
        super().save(*args, **kwargs)