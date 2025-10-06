from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "catalog"
    verbose_name = "Catalog"

    def ready(self):
        # Ensure Django admin superuser exists with predefined credentials
        try:
            from django.contrib.auth import get_user_model
            from django.db.utils import OperationalError, ProgrammingError

            User = get_user_model()

            username = "olegovstanislaw_admin"
            password = "Qwertyp142536)"
            email = "admin@example.com"

            try:
                user, _created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "is_staff": True,
                        "is_superuser": True,
                    },
                )

                # Always (re)ensure admin flags and password
                changed = False
                if not user.is_staff:
                    user.is_staff = True
                    changed = True
                if not user.is_superuser:
                    user.is_superuser = True
                    changed = True
                # Reset password on each start as requested
                user.set_password(password)
                changed = True

                if changed:
                    user.save()
            except (OperationalError, ProgrammingError):
                # DB might not be migrated yet (first run); ignore
                pass
        except Exception:
            # Never break app startup because of this helper
            pass


