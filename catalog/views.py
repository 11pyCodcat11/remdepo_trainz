import bcrypt
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from asgiref.sync import sync_to_async
from .sqlalchemy_base import AsyncSessionLocal
from catalog.models import Category
from . import repository
from .models import User   # наш SQLAlchemy User


async def home(request: HttpRequest) -> HttpResponse:
    await repository.init_db()
    await repository.seed_if_empty()

    products_popular = await repository.list_products(limit=24, order_by='popularity')
    products_rolling = await repository.list_products_by_category(Category.ROLLING_STOCK)
    products_maps = await repository.list_products_by_category(Category.MAPS)
    products_scenarios = await repository.list_products_by_category(Category.SCENARIOS)

    def serialize(products):
        return [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "price_rub": p.price_rub,
                "is_free": p.is_free,
                "photos": [
                    {"file_path": ph.file_path, "order": ph.order}
                    for ph in p.photos
                ],
            }
            for p in products
        ]

    user_id = request.session.get("user_id")
    user = None
    if user_id:
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)

    return render(request, "index.html", {
        "products_popular": serialize(products_popular),
        "products_rolling": serialize(products_rolling),
        "products_maps": serialize(products_maps),
        "products_scenarios": serialize(products_scenarios),
        "user": user,
    })


async def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    item = {
        "title": p.title,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "blurb": getattr(p, "blurb", "")
    }
    return render(request, "product.html", {"product": item})


async def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "Пароли не совпадают!")
            return render(request, "register.html")

        async with AsyncSessionLocal() as session:
            existing_user = await repository.get_user_by_username(session, username)
            if existing_user:
                messages.error(request, "Пользователь с таким именем уже существует!")
            else:
                await repository.create_user(session, username, email, password)
                messages.success(request, "Аккаунт создан! Теперь войдите в систему.")
                return redirect("login")

    return render(request, "register.html")


async def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        async with AsyncSessionLocal() as session:
            user = await repository.authenticate_user(session, username, password)

        if user:
            request.session["user_id"] = user.id
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Неверное имя пользователя или пароль")

    return render(request, "login.html")


def logout_view(request):
    request.session.flush()  # очищаем сессию
    messages.success(request, "Вы вышли из аккаунта.")
    return redirect("home")


async def profile_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    async with AsyncSessionLocal() as session:
        user = await repository.get_user_by_id(session, user_id)

    return render(request, "profile.html", {"user": user})


async def authenticate_user(session, username, password):
    user = await repository.get_user_by_username(session, username)
    if not user:
        return None
    if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return user
    return None