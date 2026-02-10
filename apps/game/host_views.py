from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Event, Participant, Signal, Match

@staff_member_required
def host_page(request):
    code = (request.GET.get("code") or "").strip()
    return render(request, "game/host.html", {"code": code})

@api_view(["GET"])
def host_snapshot(request):
    code = (request.GET.get("code") or "").strip()
    if not code:
        return Response({"error": "code 필요"}, status=400)

    event = Event.objects.filter(code=code).first()
    if not event:
        return Response({"error": "이벤트 없음"}, status=404)

    participants = (
        Participant.objects
        .filter(event=event)
        .annotate(sent_count=Count("sent_signals"))
        .order_by("nickname")
    )

    males, females = [], []
    for p in participants:
        row = {
            "id": p.id,
            "nickname": p.nickname,
            "gender": p.gender,
            "received_count": p.received_count,
            "sent_count": p.sent_count,
        }
        (males if p.gender == "M" else females).append(row)

    match_count = Match.objects.filter(event=event).count()

    return Response({
        "event": {"id": event.id, "code": event.code, "status": event.status, "message_open": event.message_open},
        "stats": {
            "participants": participants.count(),
            "signals": Signal.objects.filter(event=event).count(),
            "matches": match_count,
        },
        "males": males,
        "females": females,
    })

@staff_member_required
def toggle_event_status(request):
    code = (request.POST.get("code") or "").strip()
    event = Event.objects.filter(code=code).first()
    if not event:
        return redirect("/host/")
    event.status = "CLOSED" if event.status == "OPEN" else "OPEN"
    event.save(update_fields=["status"])
    return redirect(f"/host/?code={event.code}")

@staff_member_required
def toggle_message_open(request):
    code = (request.POST.get("code") or "").strip()
    event = Event.objects.filter(code=code).first()
    if not event:
        return redirect("/host/")
    event.message_open = not event.message_open
    event.save(update_fields=["message_open"])
    return redirect(f"/host/?code={event.code}")
