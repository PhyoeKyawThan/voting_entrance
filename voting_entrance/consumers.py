import json
from channels.generic.websocket import AsyncWebsocketConsumer

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
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'scanner_message',
                'message': f"Scanned: {qr_content}"
            }
        )

    async def scanner_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))


class ScannerStatusConsumer(AsyncWebsocketConsumer):
    active_connections = 0

    async def connect(self):
        self.group_name = "global_status"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('status') == 'active':
            ScannerStatusConsumer.active_connections += 1
            await self.broadcast_status()

    async def disconnect(self, close_code):
        if ScannerStatusConsumer.active_connections > 0:
            ScannerStatusConsumer.active_connections -= 1
        
        await self.broadcast_status()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast_status(self):
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'status_update',
                'is_active': ScannerStatusConsumer.active_connections > 0
            }
        )

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'is_active': event['is_active']
        }))