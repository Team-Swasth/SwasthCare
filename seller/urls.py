from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('edit/', views.edit_extracted_data, name='edit_extracted_data'),
]
