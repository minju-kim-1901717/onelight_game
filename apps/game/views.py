from datetime import timedelta

from django.db import transaction, models
from django.db.models import Count, F, Exists, OuterRef
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view
from rest_framework.response import Response

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Event, Participant, Signal, Match, Message
from .auth import require_participant


def _pin_valid(pin: str) -> bool:
    pin = (pin or "").strip()
    return 4 <= len(pin) <= 12


# =========================
# Auth / Join
# =========================
@csrf_exempt
@api_view(["POST"])
def join(request):
    code = (request.data.get("code") or "").strip()
    nickname = (request.data.get("nickname") or "").strip()
    gender = (request.data.get("gender") or "").strip().upper()  # M/F
    pin = (request.data.get("pin") or "").strip()

    if not code or not nickname or gender not in ("M", "F") or not _pin_valid(pin):
        return Response({"error": "code/nickname/gender(M/F)/pin(4~12) 필요"}, status=400)

    event = Event.objects.filter(code=code).first()
    if not event:
        return Response({"error": "이벤트 없음"}, status=404)
    if event.status != "OPEN":
        return Response({"error": "현재 입장이 닫혀있어요"}, status=403)

    participant = Participant.objects.filter(event=event, nickname=nickname).first()
    if participant:
        if participant.gender != gender:
            return Response({"error": "닉네임/성별 불일치"}, status=400)
        if not participant.check_pin(pin):
            return Response({"error": "비밀번호가 틀렸어요"}, status=403)
    else:
        participant = Participant(event=event, nickname=nickname, gender=gender)
        participant.set_pin(pin)
        participant.save()

    request.session["participant_id"] = participant.id
    return Response({"id": participant.id})


@api_view(["POST"])
def logout(request):
    request.session.pop("participant_id", None)
    return Response({"ok": True})


@api_view(["GET"])
def me(request):
    me_p, err = require_participant(request)
    if err:
        return err

    p = Participant.objects.annotate(sent_count=Count("sent_signals")).get(id=me_p.id)

    # 최근 매칭 1개만 보여줌(매칭 확인용)
    m = (
        Match.objects.filter(event=me_p.event)
        .filter(models.Q(p1=me_p) | models.Q(p2=me_p))
        .order_by("-created_at")
        .first()
    )
    partner = None
    if m:
        partner = m.p2 if m.p1_id == me_p.id else m.p1

    return Response(
        {
            "id": p.id,
            "event_id": p.event_id,
            "event_code": p.event.code,
            "event_status": p.event.status,
            "nickname": p.nickname,
            "gender": p.gender,
            "received_count": p.received_count,
            "sent_count": p.sent_count,
            "partner": {"id": partner.id, "nickname": partner.nickname} if partner else None,
        }
    )


# =========================
# Cards (Opposite gender list)
# =========================
@api_view(["GET"])
def list_opposites(request):
    me_p, err = require_participant(request)
    if err:
        return err

    opposite = "F" if me_p.gender == "M" else "M"

    sent_to_ids = set(
        Signal.objects.filter(event=me_p.event, from_participant=me_p).values_list(
            "to_participant_id", flat=True
        )
    )

    qs = (
        Participant.objects.filter(event=me_p.event, gender=opposite)
        .exclude(id=me_p.id)
        .order_by("nickname")
    )

    data = [{"id": p.id, "nickname": p.nickname, "sent": (p.id in sent_to_ids)} for p in qs]
    return Response({"cards": data})


# =========================
# Signal (2개 제한) + Match 생성 + 실시간
# =========================
@csrf_exempt
@api_view(["POST"])
def send_signal(request):
    me_p, err = require_participant(request)
    if err:
        return err

    to_id = request.data.get("to_id")
    if not to_id:
        return Response({"error": "to_id 필요"}, status=400)

    to_p = Participant.objects.filter(id=to_id, event=me_p.event).first()
    if not to_p:
        return Response({"error": "대상 참가자 없음"}, status=404)
    if to_p.id == me_p.id:
        return Response({"error": "본인에게는 보낼 수 없음"}, status=400)
    if me_p.gender == to_p.gender:
        return Response({"error": "이성에게만 보낼 수 있음"}, status=400)

    channel_layer = get_channel_layer()

    with transaction.atomic():
        sent_count = (
            Signal.objects.select_for_update()
            .filter(event=me_p.event, from_participant=me_p)
            .count()
        )
        if sent_count >= 2:
            return Response({"error": "시그널 2개 초과"}, status=400)

        if Signal.objects.filter(
            event=me_p.event, from_participant=me_p, to_participant=to_p
        ).exists():
            return Response({"error": "이미 보냄"}, status=400)

        Signal.objects.create(event=me_p.event, from_participant=me_p, to_participant=to_p)

        Participant.objects.filter(id=to_p.id).update(received_count=F("received_count") + 1)
        to_p.refresh_from_db(fields=["received_count"])

        # 수신자: 받은 호감 실시간
        async_to_sync(channel_layer.group_send)(
            f"participant_{to_p.id}",
            {"type": "received_update", "received_count": to_p.received_count},
        )

        # 매칭 체크(상호 시그널)
        if Signal.objects.filter(event=me_p.event, from_participant=to_p, to_participant=me_p).exists():
            a, b = Match.normalized_pair(me_p.id, to_p.id)
            match, created = Match.objects.get_or_create(event=me_p.event, p1_id=a, p2_id=b)

            if created:
                match_count = Match.objects.filter(event=me_p.event).count()

                # 두 사람에게 매칭 실시간
                async_to_sync(channel_layer.group_send)(
                    f"participant_{me_p.id}",
                    {"type": "match_created", "partner_nickname": to_p.nickname, "match_count": match_count},
                )
                async_to_sync(channel_layer.group_send)(
                    f"participant_{to_p.id}",
                    {"type": "match_created", "partner_nickname": me_p.nickname, "match_count": match_count},
                )

                # 호스트 대시보드 커플수 실시간(있으면)
                async_to_sync(channel_layer.group_send)(
                    f"event_{me_p.event_id}_host",
                    {"type": "match_count_update", "match_count": match_count},
                )

    return Response({"ok": True}, status=201)


# =========================
# 2부 메시지 기능: 10분 자동 잠금 + 1회 제한
# =========================
def _is_message_open(event: Event) -> bool:
    """
    Event 모델에 message_opened_at / message_write_open 같은 필드가 없더라도
    최소한 message_open(boolean)만 있는 구버전과 호환되게 처리.
    (운영은 message_opened_at 기반을 추천)
    """
    # ✅ 최신(추천): message_opened_at + 10분
    if hasattr(event, "message_opened_at") and hasattr(event, "message_write_open"):
        if not event.message_write_open or not event.message_opened_at:
            return False
        return timezone.now() <= event.message_opened_at + timedelta(minutes=10)

    # ✅ 구버전 호환: message_open boolean만 있으면 그걸로 판단
    if hasattr(event, "message_open"):
        return bool(event.message_open)

    return False


@api_view(["GET"])
def event_state(request):
    me_p, err = require_participant(request)
    if err:
        return err

    return Response({"message_open": _is_message_open(me_p.event)})


@api_view(["GET"])
def message_count(request):
    me_p, err = require_participant(request)
    if err:
        return err

    cnt = Message.objects.filter(event=me_p.event, to_participant=me_p).count()
    return Response({"count": cnt})


@csrf_exempt
@api_view(["POST"])
def send_message(request):
    """
    - 2부 오픈(+10분) 내에만 가능
    - 1인 1회 제한 (event + from_participant 기준)
    - 수신자는 내용 못 봄(개수만), 관리자는 admin에서 확인
    """
    me_p, err = require_participant(request)
    if err:
        return err

    if not _is_message_open(me_p.event):
        return Response({"error": "2부 메시지 시간이 종료되었어요"}, status=403)

    # 1회 제한
    if Message.objects.filter(event=me_p.event, from_participant=me_p).exists():
        return Response({"error": "메시지는 1회만 보낼 수 있어요"}, status=400)

    to_id = request.data.get("to_id")
    text = (request.data.get("text") or "").strip()

    if not to_id:
        return Response({"error": "to_id 필요"}, status=400)
    if not text:
        return Response({"error": "내용이 비었어요"}, status=400)
    if len(text) > 200:
        return Response({"error": "200자 이내로 작성해줘"}, status=400)

    to_p = Participant.objects.filter(id=to_id, event=me_p.event).first()
    if not to_p:
        return Response({"error": "대상 참가자 없음"}, status=404)
    if to_p.id == me_p.id:
        return Response({"error": "본인에게는 보낼 수 없음"}, status=400)
    if me_p.gender == to_p.gender:
        return Response({"error": "이성에게만 보낼 수 있음"}, status=400)

    Message.objects.create(
        event=me_p.event,
        from_participant=me_p,
        to_participant=to_p,
        text=text,
    )

    # ✅ 실시간으로 “개수”만 올려주고 싶으면 여기서 WS를 추가해도 됨(원하면 붙여줄게)
    return Response({"ok": True}, status=201)


@api_view(["GET"])
def matches(request):
    pid = request.session.get("participant_id")
    if not pid:
        return Response(status=401)

    me = Participant.objects.select_related("event").get(id=pid)

    # 내가 보낸(to_participant) 중, 상대가 나에게도 보낸(from_participant) 신호가 존재하면 "매칭"
    reverse_exists = Signal.objects.filter(
        event=me.event,
        from_participant=OuterRef("to_participant_id"),
        to_participant=me,
    )

    my_sent = Signal.objects.filter(event=me.event, from_participant=me).annotate(
        is_matched=Exists(reverse_exists)
    ).filter(is_matched=True)

    partner_ids = list(my_sent.values_list("to_participant_id", flat=True))
    partners = Participant.objects.filter(id__in=partner_ids).order_by("nickname")

    return Response({
        "matches": [{"id": p.id, "nickname": p.nickname} for p in partners]
    })