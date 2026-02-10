from django.shortcuts import render, redirect

def join_page(request):
    return render(request, "game/join.html")

def lobby_page(request):
    if not request.session.get("participant_id"):
        return redirect("/")
    return render(request, "game/lobby.html")

def play_page(request):
    if not request.session.get("participant_id"):
        return redirect("/")
    return render(request, "game/play.html")

def chat_page(request):
    if not request.session.get("participant_id"):
        return redirect("/")
    return render(request, "game/chat.html")

def match_page(request):
    if not request.session.get("participant_id"):
        return redirect("/")
    return render(request, "game/match.html")

def message_page(request):
    if not request.session.get("participant_id"):
        return redirect("/")
    return render(request, "game/message.html")