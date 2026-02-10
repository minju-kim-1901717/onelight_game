from django.contrib import admin
from django.utils import timezone

from .models import Event, Participant, Signal, Match, Message


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("code", "status", "message_write_open", "message_opened_at", "created_at")
    list_editable = ("status", "message_write_open")
    actions = ["open_message_phase_10min", "close_message_phase"]

    @admin.action(description="2부 메시지 오픈(10분 시작)")
    def open_message_phase_10min(self, request, queryset):
        queryset.update(message_write_open=True, message_opened_at=timezone.now())

    @admin.action(description="2부 메시지 닫기")
    def close_message_phase(self, request, queryset):
        queryset.update(message_write_open=False)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("event", "nickname", "gender", "received_count", "created_at")
    search_fields = ("nickname", "event__code")


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("event", "from_participant", "to_participant", "created_at")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("event", "p1", "p2", "created_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("event", "from_participant", "to_participant", "created_at")
