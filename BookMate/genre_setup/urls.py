from django.urls import path
from . import views

urlpatterns = [
    path('setup/', views.genre_setup_view, name='genre_setup'),
]
