from rest_framework.response import Response
from .models import Participant

def require_participant(request):
    pid = request.session.get("participant_id")
    if not pid:
        return None, Response(status=401)
    try:
        p = Participant.objects.select_related("event").get(id=pid)
    except Participant.DoesNotExist:
        request.session.pop("participant_id", None)
        return None, Response(status=401)
    return p, None
