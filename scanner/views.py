from django.shortcuts import render, get_object_or_404
from django.http.request import HttpRequest
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from .utils import verify_qr_token
from .hardware_bridge import send_to_arduino, get_arduino_status
from people.models import People
from entrances.models import Entrance

logger = logging.getLogger(__name__)


def index(request: HttpRequest):
    return render(request, "scanner/index.html")


def arduino_status(request: HttpRequest):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    return JsonResponse(get_arduino_status())


def qr_scan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            qr_content = data.get('qr_data')

            if not qr_content:
                send_to_arduino("Unknown", "FAILED", "No data provided")
                logger.warning("Scan request with no qr_data")
                return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
            people_uuid = verify_qr_token(qr_content)
            
            if people_uuid:
                person = get_object_or_404(People, id=people_uuid)

                today = timezone.now().date()
                start_of_day = datetime.combine(today, time.min)
                end_of_day = datetime.combine(today, time.max)
                existing_entrance = (
                    Entrance.objects.filter(
                        people=person,
                        time__gte=start_of_day,
                        time__lte=end_of_day,
                    )
                    .order_by('-time')
                    .first()
                )

                if existing_entrance:
                    if not send_to_arduino(person.name, "FAILED", "Already entered today"):
                        logger.warning("Arduino write failed for duplicate scan: %s", person.name)
                    return JsonResponse(
                        {
                            'status': 'denied',
                            'message': f'{person.name} already entered today.',
                            'timestamp': existing_entrance.time.strftime('%Y-%m-%d %H:%M:%S')
                        },
                        status=409,
                    )

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

                if not send_to_arduino(person.name, "SUCCESS", "Welcome"):
                    logger.warning("Arduino write failed for successful scan: %s", person.name)

                return JsonResponse({
                    'status': 'success', 
                    'message': f'Welcome, {person.name}!',
                    'timestamp': new_entrance.time.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                if not send_to_arduino("Unknown", "FAILED", "Invalid signature"):
                    logger.warning("Arduino write failed for invalid signature scan")
                return JsonResponse({'status': 'denied', 'message': 'Invalid Security Signature'}, status=403)

        except Exception as e:
            send_to_arduino("Unknown", "FAILED", str(e))
            logger.exception("Scan processing error")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)