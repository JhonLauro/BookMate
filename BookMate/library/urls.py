from django.urls import path
from . import views

urlpatterns = [
    # Dashboard and book management
    path('dashboard/', views.dashboard_view, name='dashboard'),  
    path('book/<str:olid>/', views.book_preview, name='book_preview'),
    
    # --- API routes for Open Library ---
    path('api/search/', views.search_books, name='search_books'),
    path('api/add_book/', views.add_book, name='add_book'),
    path('api/remove_book/', views.remove_book, name='remove_book'),
    path("api/update_progress/", views.update_progress, name="update_progress"),
    path('api/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('api/update_tags/', views.update_tags, name='update_tags'),
    path('api/get_user_tags/', views.get_user_tags, name='get_user_tags'),

    # Read Book
    path("api/mock-book/", views.get_mock_book, name="mock-book"),
    path("read/", views.reader_view, name="reader"),
]