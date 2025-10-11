import json
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .sqlalchemy_base import AsyncSessionLocal
from . import repository


async def cart_view(request: HttpRequest) -> HttpResponse:
    """Страница корзины"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('login')
    
    await repository.init_db()
    
    async with AsyncSessionLocal() as session:
        cart_items = await repository.get_cart_items(session, user_id)
        
        # Сериализуем данные корзины
        cart_items_data = []
        for item in cart_items:
            if item.product:  # Проверяем что товар существует
                cart_items_data.append({
                    "id": item.id,
                    "quantity": item.quantity,
                    "product": {
                        "id": item.product.id,
                        "title": item.product.title,
                        "subtitle": item.product.subtitle,
                        "slug": item.product.slug,
                        "badge": item.product.badge,
                        "price_rub": item.product.price_rub,
                        "is_free": item.product.is_free,
                        "category": item.product.category.value,
                        "photos": [
                            {
                                "file_path": photo.file_path,
                                "is_main": photo.is_main,
                                "order": photo.order
                            }
                            for photo in sorted(item.product.photos, key=lambda x: x.order)
                        ] if item.product.photos else []
                    }
                })
    
    return render(request, "cart.html", {
        "cart_items": cart_items_data,
        "cart_items_json": json.dumps(cart_items_data)
    })


async def purchases_view(request: HttpRequest) -> HttpResponse:
    """Страница покупок"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('login')
    
    await repository.init_db()
    
    async with AsyncSessionLocal() as session:
        purchases = await repository.get_user_purchases(session, user_id)
        
        # Подсчитываем общую сумму
        total_spent = sum(p.price_paid for p in purchases)
        
        # Получаем уникальные категории
        categories = list(set(p.product.category.value for p in purchases))
        
        # Сериализуем данные покупок, убирая дубликаты по товарам
        purchases_data = []
        seen_products = set()
        for purchase in purchases:
            if purchase.product and purchase.product.id not in seen_products:  # Проверяем что товар существует и не дублируется
                seen_products.add(purchase.product.id)
                purchases_data.append({
                    "id": purchase.id,
                    "price_paid": purchase.price_paid,
                    "purchase_date": purchase.purchase_date.isoformat(),
                    "product": {
                        "id": purchase.product.id,
                        "title": purchase.product.title,
                        "subtitle": purchase.product.subtitle,
                        "slug": purchase.product.slug,
                        "badge": purchase.product.badge,
                        "price_rub": purchase.product.price_rub,
                        "is_free": purchase.product.is_free,
                        "category": purchase.product.category.value,
                        "photos": [
                            {
                                "file_path": photo.file_path,
                                "is_main": photo.is_main,
                                "order": photo.order
                            }
                            for photo in sorted(purchase.product.photos, key=lambda x: x.order)
                        ] if purchase.product.photos else []
                    }
                })
    
    return render(request, "purchases.html", {
        "purchases": purchases_data,
        "purchases_json": json.dumps(purchases_data),
        "total_spent": total_spent,
        "categories": categories
    })


@csrf_exempt
@require_http_methods(["POST"])
async def remove_from_cart_api(request):
    """API для удаления товара из корзины"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
        
        if not product_id:
            return JsonResponse({"error": "ID товара не указан"}, status=400)
        
        async with AsyncSessionLocal() as session:
            await repository.remove_from_cart(session, user_id, product_id)
            return JsonResponse({"success": True, "message": "Товар удален из корзины"})
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
async def clear_cart_api(request):
    """API для очистки корзины"""
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
        
        async with AsyncSessionLocal() as session:
            await repository.clear_cart(session, user_id)
            return JsonResponse({"success": True, "message": "Корзина очищена"})
            
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
async def checkout_cart_api(request):
    """API для оформления заказа из корзины"""
    try:
        data = json.loads(request.body)
        selected_products = data.get('selected_products', [])
        
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Необходимо войти в систему"}, status=401)
        
        if not selected_products:
            return JsonResponse({"error": "Не выбрано ни одного товара"}, status=400)
        
        # Разделяем на бесплатные и платные товары
        free_products = []
        paid_products = []
        total_amount = 0
        
        for item in selected_products:
            if item['price'] == 0:
                free_products.append(item['product_id'])
            else:
                paid_products.append(item)
                total_amount += item['price']
        
        async with AsyncSessionLocal() as session:
            # Обрабатываем бесплатные товары
            for product_id in free_products:
                # Создаем запись о покупке
                await repository.create_purchase(session, user_id, product_id, 0.0)
                # Удаляем из корзины
                await repository.remove_from_cart(session, user_id, product_id)
            
            # Получаем slug'и бесплатных товаров для перенаправления
            free_slugs = []
            if free_products:
                for product_id in free_products:
                    product = await repository.get_product_by_id(session, product_id)
                    if product:
                        free_slugs.append(product.slug)
            
            # Если есть только бесплатные товары
            if not paid_products:
                return JsonResponse({
                    "success": True,
                    "free_products": free_slugs,
                    "message": "Бесплатные товары добавлены в библиотеку"
                })
            
            # Если есть платные товары - создаем платеж
            # Пока возвращаем демо-ссылку
            return JsonResponse({
                "success": True,
                "payment_url": f"/payment/demo/cart-checkout/",
                "free_products": free_slugs,
                "total_amount": total_amount
            })
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат данных"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)
