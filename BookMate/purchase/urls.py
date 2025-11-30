from django.urls import path
from . import views

urlpatterns = [
    path('buy/<str:olid>/', views.buy_book_links, name='buy_book_links'),
    path('purchase/', views.purchase_book, name='purchase_book'),
    path('history/', views.get_purchase_history, name='get_purchase_history'),
]
