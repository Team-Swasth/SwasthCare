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
    path('compare/', views.compare_products, name='compare_products'),
    
    # Enhanced AI endpoints
    path('ai/chatbot/', views.enhanced_product_chatbot, name='enhanced_product_chatbot'),
    path('ai/speech-to-text/', views.speech_to_text_api, name='speech_to_text_api'),
    path('ai/health-analysis/<str:barcode>/', views.product_health_analysis, name='product_health_analysis'),
    path('ai/alternatives/<str:barcode>/', views.get_product_alternatives, name='get_product_alternatives'),
    path('ai/meal-suggestions/<str:barcode>/', views.get_meal_suggestions, name='get_meal_suggestions'),
    path('ai/nutrition-dashboard/', views.ai_nutrition_dashboard, name='ai_nutrition_dashboard'),
]