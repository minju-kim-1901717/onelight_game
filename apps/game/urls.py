from django.urls import path
from . import views

urlpatterns = [
    path("api/join/", views.join),
    path("api/logout/", views.logout),

    path("api/me/", views.me),
    path("api/cards/", views.list_opposites),
    path("api/signal/", views.send_signal),

    path("api/event-state/", views.event_state),
    path("api/message-count/", views.message_count),
    path("api/message/", views.send_message),
]
