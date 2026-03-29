from django.shortcuts import render
from django.http.request import HttpRequest
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def index(request: HttpRequest):
    return render(request, "scanner/index.html")


def qr_scan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            qr_content = data.get('qr_data')
            return JsonResponse({'status': 'success', 'message': 'Attendance logged'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)