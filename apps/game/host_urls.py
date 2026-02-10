from django.urls import path
from . import host_views

urlpatterns = [
    path("host/", host_views.host_page),
    path("host/api/snapshot/", host_views.host_snapshot),
    path("host/toggle-status/", host_views.toggle_event_status),
    path("host/toggle-message/", host_views.toggle_message_open),
]
