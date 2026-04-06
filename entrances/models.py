from django.db import models
from people.models import People
import uuid
from django.utils.timezone import now

class Entrance(models.Model):

    entrance_id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)

    people = models.ForeignKey(
        People,
        on_delete=models.CASCADE,
        null=False,
    )

    time = models.DateTimeField(default=now)
    