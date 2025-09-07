# catalog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
        path('profile/', views.profile_view, name='profile'),  # <- добавили
]
