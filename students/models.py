from django.db import models
import uuid


class Student(models.Model):
    
    student_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    student_number = models.IntegerField(null=False)
    name = models.CharField(max_length=50)
    picture_uri = models.CharField(max_length=255)
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
    