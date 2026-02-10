# OneLight Nickname Match MVP (Django + Channels)

## Features
- Nickname-only voting (signal) with **2 signals per user**
- Opposite-gender filtering (M sees F, F sees M)
- Real-time received-count updates
- Real-time match notification when signals become mutual
- Host dashboard shows real-time couple count
- Personal PIN (4~12 chars) for re-login / prevents others from hijacking nickname
- Admin-controlled message feature (<=200 chars) after opening; messages delivered in real-time

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Setup
1) Admin: create Event with code `ONELIGHT` (status OPEN)
2) Users join: http://127.0.0.1:8000/
3) Host dashboard: login admin then http://127.0.0.1:8000/host/?code=ONELIGHT
