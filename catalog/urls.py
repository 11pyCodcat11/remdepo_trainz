# catalog/urls.py
from django.urls import path
from . import views
from . import cart_views

urlpatterns = [
    path("", views.home, name="home"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('change-login/', views.change_login, name='change_login'),
    path('api/get-password/', views.get_password, name='get_password'),
    path('api/get-real-password/', views.get_real_password, name='get_real_password'),
    path('api/verify-password/', views.verify_password, name='verify_password'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/get-product/', views.get_product_api, name='get_product_api'),
    path('api/buy-product/', views.buy_product_api, name='buy_product_api'),
    path('download/<slug:slug>/', views.download_page, name='download_page'),
    path('download/<slug:slug>/file/', views.download_file, name='download_file'),
    path('payment/demo/<slug:slug>/', views.payment_demo, name='payment_demo'),
    path('payment/demo/cart-checkout/', views.cart_payment_demo, name='cart_payment_demo'),
    path('cart/', cart_views.cart_view, name='cart'),
    path('purchases/', cart_views.purchases_view, name='purchases'),
    path('api/remove-from-cart/', cart_views.remove_from_cart_api, name='remove_from_cart_api'),
    path('api/clear-cart/', cart_views.clear_cart_api, name='clear_cart_api'),
    path('api/checkout-cart/', cart_views.checkout_cart_api, name='checkout_cart_api'),
]
