from django.urls import path
from . import views

urlpatterns = [
    path('', views.seller_home, name='seller_home'),
    path('upload/', views.upload_document, name='seller_upload'),
    path('edit/', views.edit_extracted_data, name='edit_extracted_data'),
    path('food-items/', views.list_food_items, name='list_food_items'),
    path('edit-food-item/<str:item_id>/', views.edit_food_item, name='edit_food_item'),
]
