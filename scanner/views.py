from django.shortcuts import render, get_object_or_404
from django.http.request import HttpRequest
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .utils import verify_qr_token
from people.models import People
from entrances.models import Entrance

def index(request: HttpRequest):
    return render(request, "scanner/index.html")

def qr_scan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            qr_content = data.get('qr_data')

            if not qr_content:
                return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
            people_uuid = verify_qr_token(qr_content)
            
            if people_uuid:
                person = get_object_or_404(People, id=people_uuid)
                new_entrance = Entrance.objects.create(people=person)

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "scanner_updates",
                    {
                        "type": "scanner_message",
                        "entry": {
                            "name": person.name,
                            "timestamp": new_entrance.time.strftime('%Y-%m-%d %H:%M:%S'),
                            "iso_timestamp": new_entrance.time.isoformat(),
                            "hour": new_entrance.time.hour,
                            "status": "Verified",
                        },
                    },
                )

                return JsonResponse({
                    'status': 'success', 
                    'message': f'Welcome, {person.name}!',
                    'timestamp': new_entrance.time.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                return JsonResponse({'status': 'denied', 'message': 'Invalid Security Signature'}, status=403)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)