from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='consumer_home'),
    path('scan/', views.scan_barcode, name='scan_barcode'),
    path('product/<str:barcode>/', views.product_detail, name='product_detail'),
    path('product-by-id/<str:product_id>/', views.product_detail_by_id, name='product_detail_by_id'),
    path('search/', views.search_products, name='search_products'),
    path('api/product/', views.get_product_json, name='get_product_json'),
    path('history/', views.search_history, name='search_history'),
    path('product_chatbot/', views.product_chatbot, name='product_chatbot'),
]