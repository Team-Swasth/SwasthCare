"""
URL configuration for SwasthCare project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from . import views
from django.shortcuts import render

def loading_demo_view(request):
    return render(request, 'loading_demo.html')

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("loading-demo/", loading_demo_view, name="loading_demo"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("create-seller/", views.create_seller_view, name="create_seller"),
    path("search-history/", views.search_history_view, name="search_history"),
    path("seller/", include("seller.urls")),  # Include seller app URLs
    path("consumer/", include("consumer.urls")),  # Include consumer app URLs
    path("change-password/", views.change_password_view, name="change_password"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/<str:uidb64>/<str:token>/", views.reset_password_view, name="reset_password"),
]
