from django.urls import path
from . import page_views, views


urlpatterns = [
    path("", page_views.join_page),
    path("lobby/", page_views.lobby_page),
    path("play/", page_views.play_page),
    path("match/", page_views.match_page),
    path("message/", page_views.message_page),
    path("api/matches/", views.matches)
]
