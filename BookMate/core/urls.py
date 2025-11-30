"""
URL configuration for BookMate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),  # Landing page
    path('auth/', include('sign_up.urls')),  # Registration
    path('auth/', include('login.urls')),  # Login/Logout
    path('', include('profile_page.urls')),  # Profile pages
    path('genre/', include('genre_setup.urls')),  # Genre setup
    path('purchase/', include('purchase.urls')),  # Purchase functionality
    path('', include('library.urls')),  # Library/dashboard/books
]