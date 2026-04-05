from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Entrance
from django.utils import timezone
import datetime

def index(request):
    query = request.GET.get('q', '')
    semester_filter = request.GET.get('semester', '')
    date_filter = request.GET.get('date', '') 
    entrances = Entrance.objects.select_related('student').all().order_by('-time')
    if query:
        entrances = entrances.filter(
            Q(student__name__icontains=query) | 
            Q(student__roll_no__icontains=query)
        )
    if semester_filter:
        entrances = entrances.filter(student__current_semester=semester_filter)

    if date_filter:
        try:
            target_date = datetime.datetime.strptime(date_filter, '%Y-%m-%d').date()
            entrances = entrances.filter(time__date=target_date)
        except ValueError:
            pass
    else:
        # today = timezone.now().date()
        # entrances = entrances.filter(time__date=today)
        pass
    paginator = Paginator(entrances, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'semester_filter': semester_filter,
        'date_filter': date_filter,
    }

    return render(request, 'entrances/index.html', context)