from django.urls import path
from .consumers import ParticipantConsumer, HostConsumer

websocket_urlpatterns = [
    path("ws/participant/<int:pid>/", ParticipantConsumer.as_asgi()),
    path("ws/host/<int:event_id>/", HostConsumer.as_asgi()),
]
