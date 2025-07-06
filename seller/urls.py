from django.urls import path
from . import views

urlpatterns = [
    path('', views.seller_home, name='seller_home'),
    path('upload/', views.upload_document, name='seller_upload'),
    path('edit/', views.edit_extracted_data, name='edit_extracted_data'),
]
