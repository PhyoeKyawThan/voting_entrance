import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone


SCANNER_ACTIVE_COUNT_KEY = "scanner_status_active_count"
SCANNER_IS_ACTIVE_KEY = "scanner_status_is_active"
SCANNER_LAST_SIGNAL_KEY = "scanner_status_last_signal_at"
SCANNER_LAST_QR_KEY = "scanner_last_qr_data"

class ScannerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "scanner_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        qr_content = data.get('qr_data')
        cache.set(SCANNER_LAST_SIGNAL_KEY, timezone.now().isoformat(), timeout=None)
        if qr_content is not None:
            cache.set(SCANNER_LAST_QR_KEY, qr_content, timeout=None)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'scanner_message',
                'message': f"Scanned: {qr_content}"
            }
        )

    async def scanner_message(self, event):
        response = {}
        if 'message' in event:
            response['message'] = event['message']
        if 'entry' in event:
            response['entry'] = event['entry']

        await self.send(text_data=json.dumps(response))


class ScannerStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "global_status"
        self.is_counted_as_active = False
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_cached_status()

    async def receive(self, text_data):
        data = json.loads(text_data)
        status = data.get('status')

        if status == 'active':
            cache.set(SCANNER_LAST_SIGNAL_KEY, timezone.now().isoformat(), timeout=None)
            if not self.is_counted_as_active:
                self.increment_active_count()
                self.is_counted_as_active = True
            await self.broadcast_status()
        elif status == 'inactive' and self.is_counted_as_active:
            self.decrement_active_count()
            self.is_counted_as_active = False
            await self.broadcast_status()

    async def disconnect(self, close_code):
        if self.is_counted_as_active:
            self.decrement_active_count()
            self.is_counted_as_active = False
        
        await self.broadcast_status()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast_status(self):
        active_count = self.get_active_count()
        is_active = active_count > 0
        cache.set(SCANNER_IS_ACTIVE_KEY, is_active, timeout=None)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'status_update',
                'is_active': is_active,
                'active_count': active_count,
                'last_signal_at': cache.get(SCANNER_LAST_SIGNAL_KEY)
            }
        )

    async def send_cached_status(self):
        await self.send(text_data=json.dumps({
            'is_active': cache.get(SCANNER_IS_ACTIVE_KEY, False),
            'active_count': self.get_active_count(),
            'last_signal_at': cache.get(SCANNER_LAST_SIGNAL_KEY)
        }))

    def get_active_count(self):
        return int(cache.get(SCANNER_ACTIVE_COUNT_KEY, 0) or 0)

    def increment_active_count(self):
        if cache.get(SCANNER_ACTIVE_COUNT_KEY) is None:
            cache.add(SCANNER_ACTIVE_COUNT_KEY, 0, timeout=None)

        try:
            cache.incr(SCANNER_ACTIVE_COUNT_KEY)
        except ValueError:
            cache.set(SCANNER_ACTIVE_COUNT_KEY, 1, timeout=None)

    def decrement_active_count(self):
        current = self.get_active_count()
        if current <= 1:
            cache.set(SCANNER_ACTIVE_COUNT_KEY, 0, timeout=None)
            return

        try:
            cache.decr(SCANNER_ACTIVE_COUNT_KEY)
        except ValueError:
            cache.set(SCANNER_ACTIVE_COUNT_KEY, max(current - 1, 0), timeout=None)

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'is_active': event['is_active'],
            'active_count': event.get('active_count', 0),
            'last_signal_at': event.get('last_signal_at')
        }))