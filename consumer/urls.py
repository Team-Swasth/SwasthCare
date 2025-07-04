from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='consumer_home'),
    path('scan/', views.scan_barcode, name='scan_barcode'),
    path('product/<str:barcode>/', views.product_detail, name='product_detail'),
    path('api/product/', views.get_product_json, name='get_product_json'),
]