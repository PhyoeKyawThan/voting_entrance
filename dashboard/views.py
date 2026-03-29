from django.shortcuts import render
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from students.models import Student

@login_required
def dashboard_view(request: HttpRequest):
    student_count = Student.objects.count()
    return render(request, 'dashboard/index.html', {
        "registered_student": student_count
    })