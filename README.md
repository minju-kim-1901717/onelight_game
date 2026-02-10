# OneLight Game 🎉

솔로 파티용 실시간 시그널 & 매칭 & 메시지 시스템

> **ONE LIGHT 파티**에서 사용하는 웹 기반 참여형 게임 서비스
> 참가자는 닉네임만으로 참여하며,
> **1부(시그널) / 2부(메시지)** 구조로 자연스럽게 진행됩니다.

---

## 🧩 주요 기능 요약

### 1부 – 시그널 (호감 보내기)

* 닉네임 기반 참여 (얼굴 노출 없음)
* 남/여 성별 구분
* 이성에게만 시그널 전송 가능
* 참가자 1인당 **시그널 2개 제한**
* 상호 시그널 시 **자동 매칭**
* 매칭 결과는 참가자 본인만 확인 가능

### 2부 – 메시지 (관리자 오픈)

* 관리자가 2부를 오픈하면 메시지 기능 활성화
* **오픈 후 10분간만 메시지 전송 가능**
* 참가자 1인당 **메시지 1회 제한**
* 메시지 내용:

  * 참가자 ❌ 내용 확인 불가
  * 참가자 ✅ 받은 메시지 “개수”만 확인
  * 관리자 ✅ 전체 메시지 내용 확인 가능
* 10분 경과 시 자동 잠금 (서버 시간 기준)

---

## 🖥️ 주요 화면

| 화면          | 설명                               |
| ----------- | -------------------------------- |
| `/`         | 입장 페이지 (이벤트 코드, 닉네임, 성별, PIN 입력) |
| `/lobby/`   | 로비 (호감 수, 시그널 수, 매칭/메시지 버튼)      |
| `/play/`    | 시그널 보내기                          |
| `/match/`   | 매칭 확인                            |
| `/message/` | 메시지 보내기 (2부 오픈 시)                |
| `/admin/`   | 관리자 페이지                          |

---

## 🔐 보안 & 운영 정책

* 닉네임 + PIN 기반 재접속 보호
* 다른 참가자 접근 불가
* 메시지/매칭은 **본인에게만 노출**
* 2부 메시지 오픈/종료는 **관리자 컨트롤**
* 시간 제한은 **서버 기준** (프론트 조작 불가)

---

## 🛠️ 기술 스택

* **Backend**: Django, Django REST Framework
* **Realtime**: Django Channels (선택적)
* **DB**: SQLite (기본) / PostgreSQL (운영 권장)
* **Frontend**: HTML + Vanilla JS
* **Auth**: Session 기반

---

## 📁 프로젝트 구조

```
onelight_game/
├── Game/                 # Django 프로젝트 설정
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   └── game/             # 메인 앱
│       ├── models.py
│       ├── views.py
│       ├── admin.py
│       ├── page_views.py
│       ├── page_urls.py
│       ├── urls.py
│       └── templates/
│           └── game/
│               ├── join.html
│               ├── lobby.html
│               ├── play.html
│               ├── match.html
│               └── message.html
├── manage.py
└── db.sqlite3
```

---

## 🚀 로컬 실행 방법

### 1️⃣ 가상환경 및 패키지 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ DB 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3️⃣ 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 4️⃣ 서버 실행

```bash
python manage.py runserver
```

---

## 🧑‍💼 관리자 사용 가이드

### 이벤트 생성

1. `/admin/` 접속
2. Event 생성

   * code: 입장 코드
   * status: `OPEN`

### 2부 메시지 오픈

* Admin > Event 목록
* 이벤트 선택
* **“2부 메시지 오픈(10분 시작)”** 액션 실행

### 관리자에서 확인 가능한 정보

* 참가자 목록
* 시그널 기록
* 매칭 커플
* 메시지 전체 내용

---

## ⚠️ 운영 시 주의사항

* 메시지 오픈은 **10분 자동 종료** → 재오픈 시 다시 액션 실행 필요
* 실운영 시 SQLite 대신 **PostgreSQL 권장**
* 실시간 기능 사용 시 Redis + ASGI 서버 필요

---

## 📌 향후 확장 아이디어

* 남/여 1등 매칭 이벤트
* 메시지 우선권
* 실시간 카운트다운 표시
* 관리자 대시보드 실시간 통계
* 익명 메시지 공개 타이밍 컨트롤

---

## ✨ 한 줄 요약

> **강요 없는 솔로 파티를 위한, 가장 안전하고 자연스러운 매칭 게임 시스템**
