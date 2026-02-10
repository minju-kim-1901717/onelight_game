from django.apps import AppConfig
import os


class GameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.game"

    def ready(self):
        # 앱 로딩 중 반복 실행/에러 방지
        if os.environ.get("AUTO_CREATE_SUPERUSER") != "1":
            return

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            username = os.environ.get("ADMIN_USERNAME", "onelight")
            password = os.environ.get("ADMIN_PASSWORD", "onelight0212")
            email = os.environ.get("ADMIN_EMAIL", "admin@onelight.com")

            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "is_staff": True, "is_superuser": True},
            )

            # 있든 없든 비번/권한을 강제로 맞춤
            user.is_staff = True
            user.is_superuser = True
            user.email = email
            user.set_password(password)
            user.save()

            print(f"[AUTO_CREATE_SUPERUSER] ready: {username} created={created}")
        except Exception as e:
            print("Superuser auto-create failed:", e)
