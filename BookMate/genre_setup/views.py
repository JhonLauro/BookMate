from django.shortcuts import render, redirect
from django.contrib import messages
from profile_page.models import UserProfile


def genre_setup_view(request):
    """Handle user's favorite genres setup"""
    if not request.user.is_authenticated:
        return redirect('landing')
    
    if request.method == "POST":
        selected_genres = request.POST.getlist("genres")
        if selected_genres:
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            # Save selected genres as comma-separated string
            profile.favorite_genres = ", ".join(selected_genres)
            profile.save()
            messages.success(request, f"Favorite genres saved! ({len(selected_genres)} genres selected)")
        return redirect('dashboard')
    return render(request, 'genre_setup.html')
