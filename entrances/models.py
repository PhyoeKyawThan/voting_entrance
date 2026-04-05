from django.db import models
from students.models import Student
import uuid
from django.utils.timezone import now

class Entrance(models.Model):

    entrance_id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=False,
    )

    time = models.DateTimeField(default=now)
    