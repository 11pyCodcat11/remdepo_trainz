import json
import uuid
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from asgiref.sync import sync_to_async
from .sqlalchemy_base import AsyncSessionLocal
from catalog.models import Category
from . import repository
from .models import User   # наш SQLAlchemy User

# Настройки ЮKassa (в реальном проекте должны быть в settings.py)
YOOKASSA_SHOP_ID = "your_shop_id"  # Замените на ваш ID магазина
YOOKASSA_SECRET_KEY = "your_secret_key"  # Замените на ваш секретный ключ


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
    purchased_product_ids = set()
    if user_id:
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)
            # Получаем список купленных товаров
            purchases = await repository.get_user_purchases(session, user_id)
            purchased_product_ids = {p.product.id for p in purchases if p.product}

    # Определяем вариант отображения (desktop/tablet/mobile)
    def _detect_variant(req: HttpRequest) -> str:
        # Allow explicit override via query param for testing: ?variant=mobile|tablet|desktop
        variant_override = (req.GET.get("variant") or "").lower()
        if variant_override in {"mobile", "tablet", "desktop"}:
            return variant_override
        ua = (req.META.get("HTTP_USER_AGENT") or "").lower()
        if any(k in ua for k in ["iphone", "android", "mobile", "windows phone"]):
            return "mobile"
        if any(k in ua for k in ["ipad", "tablet", "sm-t", "lenovo tab", "mi pad"]):
            return "tablet"
        return "desktop"

    variant = _detect_variant(request)

    template_name = "mobile/index.html" if variant == "mobile" else "desktop/index.html"
    return render(request, template_name, {
        "products_popular": serialize(products_popular),
        "products_rolling": serialize(products_rolling),
        "products_maps": serialize(products_maps),
        "products_scenarios": serialize(products_scenarios),
        "user": user,
        "variant": variant,
        "purchased_product_ids": list(purchased_product_ids),
    })


async def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    # Получаем информацию о пользователе для корзины
    user_id = request.session.get("user_id")
    user = None
    if user_id:
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)
    
    # Детект варианта
    def _detect_variant(req: HttpRequest) -> str:
        variant_override = (req.GET.get("variant") or "").lower()
        if variant_override in {"mobile", "tablet", "desktop"}:
            return variant_override
        ua = (req.META.get("HTTP_USER_AGENT") or "").lower()
        if any(k in ua for k in ["iphone", "android", "mobile", "windows phone"]):
            return "mobile"
        if any(k in ua for k in ["ipad", "tablet", "sm-t", "lenovo tab", "mi pad"]):
            return "tablet"
        return "desktop"

    variant = _detect_variant(request)

    return render(request, "product.html", {
        "product": product_data,
        "user": user,
        "variant": variant
    })


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

    # Детект варианта
    def _detect_variant(req: HttpRequest) -> str:
        ua = (req.META.get("HTTP_USER_AGENT") or "").lower()
        if any(k in ua for k in ["iphone", "android", "mobile", "windows phone"]):
            return "mobile"
        if any(k in ua for k in ["ipad", "tablet", "sm-t", "lenovo tab", "mi pad"]):
            return "tablet"
        return "desktop"

    variant = _detect_variant(request)
    return render(request, "register.html", {"variant": variant})


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

    def _detect_variant(req: HttpRequest) -> str:
        ua = (req.META.get("HTTP_USER_AGENT") or "").lower()
        if any(k in ua for k in ["iphone", "android", "mobile", "windows phone"]):
            return "mobile"
        if any(k in ua for k in ["ipad", "tablet", "sm-t", "lenovo tab", "mi pad"]):
            return "tablet"
        return "desktop"

    variant = _detect_variant(request)
    return render(request, "login.html", {"variant": variant})


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

    def _detect_variant(req: HttpRequest) -> str:
        ua = (req.META.get("HTTP_USER_AGENT") or "").lower()
        if any(k in ua for k in ["iphone", "android", "mobile", "windows phone"]):
            return "mobile"
        if any(k in ua for k in ["ipad", "tablet", "sm-t", "lenovo tab", "mi pad"]):
            return "tablet"
        return "desktop"

    variant = _detect_variant(request)
    return render(request, "profile.html", {"user": user, "variant": variant})


async def authenticate_user(session, username, password):
    user = await repository.get_user_by_username(session, username)
    if not user:
        return None
    from .utils import verify_password
    if verify_password(password, user.password_hash):
        return user
    return None


@csrf_exempt
@require_http_methods(["POST"])
async def change_password(request):
    """API endpoint для смены пароля"""
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        print(f"DEBUG: Получены данные - current_password: '{current_password}', new_password: '{new_password}'")
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Пользователь не авторизован"}, status=401)
        
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)
            if not user:
                return JsonResponse({"error": "Пользователь не найден"}, status=404)
            
            # Проверяем текущий пароль
            from .utils import verify_password, hash_password
            print(f"DEBUG: Проверяем пароль '{current_password}' против хеша '{user.password_hash[:50]}...'")
            is_valid = verify_password(current_password, user.password_hash)
            print(f"DEBUG: Результат проверки: {is_valid}")
            if not is_valid:
                return JsonResponse({"error": "Неверный текущий пароль"}, status=400)
            
            # Обновляем пароль
            user.password_hash = hash_password(new_password)
            await session.commit()
            
            return JsonResponse({"success": True, "message": "Пароль успешно изменен"})
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })


@csrf_exempt
@require_http_methods(["POST"])
async def change_login(request):
    """API endpoint для смены логина"""
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_login = data.get('new_login')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Пользователь не авторизован"}, status=401)
        
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)
            if not user:
                return JsonResponse({"error": "Пользователь не найден"}, status=404)
            
            # Проверяем текущий пароль
            from .utils import verify_password
            print(f"DEBUG LOGIN: Проверяем пароль '{current_password}' против хеша '{user.password_hash[:50]}...'")
            is_valid = verify_password(current_password, user.password_hash)
            print(f"DEBUG LOGIN: Результат проверки: {is_valid}")
            if not is_valid:
                return JsonResponse({"error": "Неверный текущий пароль"}, status=400)
            
            # Проверяем, не занят ли новый логин
            existing_user = await repository.get_user_by_username(session, new_login)
            if existing_user and existing_user.id != user.id:
                return JsonResponse({"error": "Пользователь с таким логином уже существует"}, status=400)
            
            # Обновляем логин
            user.username = new_login
            await session.commit()
            
            return JsonResponse({"success": True, "message": "Логин успешно изменен"})
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })


@csrf_exempt
@require_http_methods(["POST"])
async def verify_password(request):
    """API endpoint для проверки пароля"""
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Пользователь не авторизован"}, status=401)
        
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)
            if not user:
                return JsonResponse({"error": "Пользователь не найден"}, status=404)
            
            # Проверяем пароль
            from .utils import verify_password
            if verify_password(password, user.password_hash):
                return JsonResponse({"valid": True})
            else:
                return JsonResponse({"valid": False, "error": "Неверный пароль"}, status=400)
                
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })


@csrf_exempt
@require_http_methods(["POST"])
async def get_real_password(request):
    """API endpoint для получения реального пароля после подтверждения"""
    try:
        data = json.loads(request.body)
        confirm_password = data.get('confirm_password')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Пользователь не авторизован"}, status=401)
        
        async with AsyncSessionLocal() as session:
            user = await repository.get_user_by_id(session, user_id)
            if not user:
                return JsonResponse({"error": "Пользователь не найден"}, status=404)
            
            # Проверяем подтверждающий пароль
            from .utils import verify_password
            if not verify_password(confirm_password, user.password_hash):
                return JsonResponse({"error": "Неверный пароль"}, status=400)
            
            # Возвращаем реальный пароль
            return JsonResponse({"password": confirm_password})
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })


@require_http_methods(["GET"])
async def get_password(request):
    """API endpoint для получения пароля (устаревший)"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Пользователь не авторизован"}, status=401)
    
    # Возвращаем заглушку - реальный пароль получается через get_real_password
    return JsonResponse({"password": "********"})


@csrf_exempt
@require_http_methods(["POST"])
async def add_to_cart(request):
    """Добавить товар в корзину"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
        
        if not product_id:
            return JsonResponse({"error": "ID товара не указан"}, status=400)
        
        async with AsyncSessionLocal() as session:
            # Проверяем существование пользователя
            user = await repository.get_user_by_id(session, user_id)
            if not user:
                return JsonResponse({"error": "Пользователь не найден"}, status=404)
            
            # Проверяем существование товара
            product = await repository.get_product_by_id(session, product_id)
            if not product:
                return JsonResponse({"error": "Товар не найден"}, status=404)
            
            # Добавляем в корзину
            await repository.add_to_cart(session, user_id, product_id)
            
            return JsonResponse({"message": "Товар добавлен в корзину"})
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })


@csrf_exempt
@require_http_methods(["POST"])
async def get_product_api(request):
    """Получить бесплатный товар"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
        
        if not product_id:
            return JsonResponse({"error": "ID товара не указан"}, status=400)
        
        async with AsyncSessionLocal() as session:
            # Проверяем существование товара
            product = await repository.get_product_by_id(session, product_id)
            if not product:
                return JsonResponse({"error": "Товар не найден"}, status=404)
            
            if not product.is_free:
                return JsonResponse({"error": "Этот товар не бесплатный"}, status=400)
            
            # Создаем запись о получении бесплатного товара
            await repository.create_purchase(session, user_id, product_id, 0.0)
            
            return JsonResponse({
                "message": "Товар успешно получен", 
                "download_url": f"/download/{product.slug}/",
                "product_slug": product.slug,
                "product_id": product.id
            })
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })


async def cart_payment_demo(request: HttpRequest) -> HttpResponse:
    """Демо страница оплаты для корзины"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    # Создаем фиктивный товар для демо-оплаты корзины
    cart_product = {
        "title": "Товары из корзины",
        "subtitle": "Выбранные товары для покупки",
        "category": "Корзина",
        "price_rub": 100,  # Можно получить из сессии или параметров
        "slug": "cart-items",
        "photos": []
    }
    
    return render(request, "payment_demo.html", {
        "product": cart_product
    })


@csrf_exempt
@require_http_methods(["POST"])
async def buy_product_api(request):
    """Создать платеж через ЮKassa"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
        
        if not product_id:
            return JsonResponse({"error": "ID товара не указан"}, status=400)
        
        async with AsyncSessionLocal() as session:
            # Проверяем существование товара и пользователя
            product = await repository.get_product_by_id(session, product_id)
            user = await repository.get_user_by_id(session, user_id)
            
            if not product:
                return JsonResponse({"error": "Товар не найден"}, status=404)
            
            if not user:
                return JsonResponse({"error": "Пользователь не найден"}, status=404)
            
            if product.is_free:
                return JsonResponse({"error": "Этот товар бесплатный"}, status=400)
            
            # Создаем платеж через ЮKassa
            try:
                from yookassa import Configuration, Payment
                
                # Настройка ЮKassa
                Configuration.account_id = YOOKASSA_SHOP_ID
                Configuration.secret_key = YOOKASSA_SECRET_KEY
                
                # Создаем уникальный ID для платежа
                idempotence_key = str(uuid.uuid4())
                
                # Создаем платеж
                payment = Payment.create({
                    "amount": {
                        "value": str(product.price_rub),
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": f"{request.build_absolute_uri('/').rstrip('/')}/payment/success/{product.slug}/"
                    },
                    "capture": True,
                    "description": f"Покупка товара: {product.title}",
                    "metadata": {
                        "product_id": str(product.id),
                        "user_id": str(user.id),
                        "product_slug": product.slug
                    }
                }, idempotence_key)
                
                # Сохраняем информацию о платеже в сессии
                request.session[f'payment_{payment.id}'] = {
                    'product_id': product.id,
                    'user_id': user.id,
                    'amount': product.price_rub
                }
                
                return JsonResponse({
                    "success": True,
                    "payment_url": payment.confirmation.confirmation_url,
                    "payment_id": payment.id
                })
                
            except Exception as payment_error:
                # В случае ошибки ЮKassa возвращаем заглушку для демонстрации
                return JsonResponse({
                    "success": True,
                    "payment_url": f"/payment/demo/{product.slug}/",
                    "payment_id": f"demo_{product_id}_{user_id}",
                    "demo_mode": True,
                    "message": "Демо-режим: ЮKassa не настроена"
                })
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


async def download_page(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница скачивания для товаров"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - перенаправляем на страницу товара
    if not p.is_free and not is_purchased:
        messages.error(request, "Сначала необходимо приобрести этот товар")
        return redirect('product_detail', slug=slug)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "download.html", {
        "product": product_data
    })


async def download_file(request: HttpRequest, slug: str) -> HttpResponse:
    """API для скачивания файла"""
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
    
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return JsonResponse({"error": "Товар не найден"}, status=404)
    
    # Проверяем, куплен ли товар пользователем
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        is_purchased = any(purchase.product.id == p.id for purchase in purchases if purchase.product)
    
    # Если товар платный и не куплен - возвращаем ошибку
    if not p.is_free and not is_purchased:
        return JsonResponse({"error": "Сначала необходимо приобрести этот товар"}, status=403)
    
    # Здесь должна быть логика для реального скачивания файла
    # Пока возвращаем заглушку
    from django.http import HttpResponse
    
    # Имитация файла
    response = HttpResponse(
        content=f"Файл {p.title} (.trainz-package)\nЭто демо-версия файла.",
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{p.slug}.trainz-package"'
    
    return response


async def payment_demo(request: HttpRequest, slug: str) -> HttpResponse:
    """Демо-страница оплаты"""
    await repository.init_db()
    p = await repository.get_product(slug)
    if not p:
        return render(request, "404.html", status=404)
    
    # Сериализуем продукт с фотографиями
    product_data = {
        "id": p.id,
        "title": p.title,
        "subtitle": p.subtitle,
        "slug": p.slug,
        "badge": p.badge,
        "price_rub": p.price_rub,
        "is_free": p.is_free,
        "category": p.category.value,
        "blurb": p.blurb,
        "photos": [
            {
                "file_path": photo.file_path,
                "is_main": photo.is_main,
                "order": photo.order
            }
            for photo in sorted(p.photos, key=lambda x: x.order)
        ] if p.photos else []
    }
    
    return render(request, "payment_demo.html", {
        "product": product_data
    })

async def payment_success(request: HttpRequest, slug: str) -> HttpResponse:
    """Обработка успешной оплаты"""
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Необходимо войти в систему")
        return redirect('login')
    
    await repository.init_db()
    
    async with AsyncSessionLocal() as session:
        # Получаем товар
        product = await repository.get_product(slug)
        if not product:
            return render(request, "404.html", status=404)
        
        # Проверяем, не куплен ли уже товар
        purchases = await repository.get_user_purchases(session, user_id)
        already_purchased = any(p.product.id == product.id for p in purchases if p.product)
        
        if not already_purchased:
            # Создаем запись о покупке
            await repository.create_purchase(session, user_id, product.id, product.price_rub)
            messages.success(request, f"Товар '{product.title}' успешно приобретен!")
        else:
            messages.info(request, f"Товар '{product.title}' уже был приобретен ранее")
        
        # Перенаправляем на страницу скачивания
        return redirect('download_page', slug=slug)
