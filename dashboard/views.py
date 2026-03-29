from django.shortcuts import render
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from students.models import Student, EntranceQR

@login_required
def dashboard_view(request: HttpRequest):
    student_count = Student.objects.count()
    active_qrs_count = EntranceQR.objects.filter(is_active=1).count()
    
    return render(request, 'dashboard/index.html', {
        "registered_student": student_count,
        "active_qr_percentage": ( active_qrs_count / student_count ) * 100
    })