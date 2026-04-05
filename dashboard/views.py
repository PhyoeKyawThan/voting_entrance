from django.shortcuts import render
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from students.models import Student, EntranceQR
from entrances.models import Entrance
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import ExtractHour

@login_required
def dashboard_view(request):
    current_tz = timezone.get_current_timezone()
    local_now = timezone.localtime(timezone.now())
    today = local_now.date()

    student_count = Student.objects.count()
    active_qrs_count = EntranceQR.objects.filter(is_active=True).count()
    
    hourly_data = (
        Entrance.objects.filter(time__date=today)
        .annotate(hour=ExtractHour('time', tzinfo=current_tz))
        .values('hour')
        .annotate(count=Count('entrance_id'))
        .order_by('hour')
    )
    
    traffic_dict = {item['hour']: item['count'] for item in hourly_data}
    chart_labels = ["9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM"]
    chart_data = [traffic_dict.get(h, 0) for h in range(9, 17)]
    
    active_percentage = (active_qrs_count / student_count * 100) if student_count > 0 else 0
    print(hourly_data)
    return render(request, 'dashboard/index.html', {
        "registered_student": student_count,
        "active_qr_percentage": round(active_percentage, 1),
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    })