from datetime import timedelta

from django.db import models
from django.utils import timezone


class Event(models.Model):
    STATUS_CHOICES = (
        ("OPEN", "OPEN"),
        ("CLOSED", "CLOSED"),
    )

    code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")

    # 2부 메시지 기능 오픈(서버시간 기준)
    # - 관리자가 오픈하면 message_write_open=True, message_opened_at=now()
    # - 10분 지나면 자동 잠금
    message_write_open = models.BooleanField(default=False)
    message_opened_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_message_open(self) -> bool:
        if not self.message_write_open or not self.message_opened_at:
            return False
        return timezone.now() <= self.message_opened_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.code} ({self.status})"


class Participant(models.Model):
    GENDER_CHOICES = (("M", "남"), ("F", "여"))

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=30)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    # 간단 PIN(현재 프로젝트에서 auth.py가 set_pin/check_pin을 제공한다고 가정)
    pin_hash = models.CharField(max_length=200, blank=True, default="")

    received_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "nickname")

    # auth.py에 이미 구현돼 있을 수도 있지만, 없으면 여기로 사용 가능
    def set_pin(self, raw_pin: str):
        # 매우 단순 해시(운영에서는 PBKDF2/BCrypt 권장)
        # 지금 프로젝트는 "운영 급하게"가 목적이라 최소 구현
        import hashlib
        self.pin_hash = hashlib.sha256(raw_pin.encode("utf-8")).hexdigest()

    def check_pin(self, raw_pin: str) -> bool:
        import hashlib
        return self.pin_hash == hashlib.sha256(raw_pin.encode("utf-8")).hexdigest()

    def __str__(self):
        return f"[{self.event.code}] {self.nickname}"


class Signal(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    from_participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="sent_signals"
    )
    to_participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="received_signals"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_participant.nickname} → {self.to_participant.nickname}"


class Match(models.Model):
    """
    상호 시그널 성립 시 생성되는 매칭.
    (p1, p2)는 항상 작은 id, 큰 id로 정규화해서 중복 방지.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    p1 = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="match_p1"
    )
    p2 = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="match_p2"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "p1", "p2")

    @staticmethod
    def normalized_pair(a_id: int, b_id: int):
        return (a_id, b_id) if a_id < b_id else (b_id, a_id)

    def __str__(self):
        return f"[{self.event.code}] {self.p1.nickname} ❤ {self.p2.nickname}"


class Message(models.Model):
    """
    2부 메시지: 참가자 1회 제한
    - unique_together(event, from_participant)
    - 수신자는 '개수'만 확인, 내용은 admin에서만 확인
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    from_participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="sent_messages"
    )
    to_participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="received_messages"
    )
    text = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "from_participant")

    def __str__(self):
        return f"{self.from_participant.nickname} → {self.to_participant.nickname}"
