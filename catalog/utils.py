from django.contrib.auth.hashers import make_password, check_password


def hash_password(raw_password: str) -> str:
    """Создаёт безопасный хэш пароля (для хранения в БД)."""
    return make_password(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Проверяет введённый пароль против хэша из БД."""
    return check_password(raw_password, hashed_password)
