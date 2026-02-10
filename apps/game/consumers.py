from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ParticipantConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.pid = self.scope["url_route"]["kwargs"]["pid"]
        self.group_name = f"participant_{self.pid}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def received_update(self, event):
        await self.send_json({"type": "received_update", "received_count": event["received_count"]})

    async def match_created(self, event):
        await self.send_json({"type": "match_created", "partner_nickname": event["partner_nickname"], "match_count": event.get("match_count")})

    async def message_received(self, event):
        await self.send_json({"type": "message_received", "from_nickname": event["from_nickname"], "text": event["text"], "created_at": event.get("created_at")})

class HostConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope["url_route"]["kwargs"]["event_id"]
        self.group_name = f"event_{self.event_id}_host"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def match_count_update(self, event):
        await self.send_json({"type": "match_count_update", "match_count": event["match_count"]})

    async def stats_update(self, event):
        await self.send_json({"type": "stats_update", **event["payload"]})
