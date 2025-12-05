from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import F
from django.conf import settings
from .models import UserProfile
from library.models import UserBookList
from supabase import create_client, Client
import uuid
import os


def profile_view(request):
    """Display user profile with stats and books"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Refresh user data from database
    user = User.objects.get(pk=request.user.pk)
    
    # Get user's books
    user_books = UserBookList.objects.filter(user=user)
    
    # Calculate stats
    total_books = user_books.count()
    books_with_progress = user_books.exclude(current_page__gte=F('pages'), pages__gt=0)  # Show all books except finished ones
    finished_books = user_books.filter(current_page__gte=F('pages'), pages__gt=0)
    favorite_books = user_books.filter(is_favorite=True)
    
    # Get user's favorite genres and profile picture from profile
    user_favorite_genres = []
    profile_picture_url = None
    user_bio = None
    try:
        profile = UserProfile.objects.get(user=user)
        user_favorite_genres = profile.get_favorite_genres_list()
        profile_picture_url = profile.profile_picture_url
        user_bio = profile.bio
    except UserProfile.DoesNotExist:
        user_favorite_genres = []
        profile_picture_url = None
        user_bio = None
    
    context = {
        'user': user,
        'total_books': total_books,
        'currently_reading': books_with_progress.count(),
        'finished_books': finished_books.count(),
        'favorite_books_count': favorite_books.count(),
        'user_favorite_genres': user_favorite_genres,
        'profile_picture_url': profile_picture_url,
        'user_bio': user_bio,
        'reading_books': books_with_progress[:100],  # Show 100 currently reading
        'completed_books': finished_books[:100],  # Show 100 finished
        'favorite_books': favorite_books[:100],  # Show 100 favorite books
    }
    
    return render(request, 'profile.html', context)


def edit_profile_view(request):
    """Edit user profile information"""
    if not request.user.is_authenticated:
        return redirect('login')

    # Always get fresh user data from database
    user = User.objects.get(pk=request.user.pk)
    
    # Get user profile for profile picture (always fetch fresh)
    profile_picture_url = None
    try:
        profile = UserProfile.objects.get(user=user)
        profile_picture_url = profile.profile_picture_url
    except UserProfile.DoesNotExist:
        profile_picture_url = None

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Check if username is taken by another user
        if username != user.username and User.objects.filter(username=username).exists():
            try:
                profile = UserProfile.objects.get(user=user)
                profile_picture_url = profile.profile_picture_url
            except UserProfile.DoesNotExist:
                profile_picture_url = None
            return render(request, 'edit_profile.html', {
                "user": user,
                "profile_picture_url": profile_picture_url,
                "error_message": "Username already taken!"
            })

        # Update basic info
        user.username = username
        user.email = email

        # Handle password update (optional)
        password_changed = False
        if password1 and password1 == password2:
            user.set_password(password1)
            password_changed = True
        elif password1 or password2:
            # Refresh profile picture URL before re-rendering
            try:
                profile = UserProfile.objects.get(user=user)
                profile_picture_url = profile.profile_picture_url
            except UserProfile.DoesNotExist:
                profile_picture_url = None
            return render(request, 'edit_profile.html', {
                "user": user,
                "profile_picture_url": profile_picture_url,
                "error_message": "Passwords do not match!"
            })

        try:
            user.save()
            # Re-authenticate the user after password change
            if password_changed:
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
            
            # Redirect with success parameter
            from django.shortcuts import redirect
            from django.urls import reverse
            if password_changed:
                return redirect(reverse('profile') + '?updated=password')
            return redirect(reverse('profile') + '?updated=success')
        except Exception as e:
            # Handle any other database errors
            try:
                profile = UserProfile.objects.get(user=user)
                profile_picture_url = profile.profile_picture_url
            except UserProfile.DoesNotExist:
                profile_picture_url = None
            return render(request, 'edit_profile.html', {
                "user": user,
                "profile_picture_url": profile_picture_url,
                "error_message": "Error updating profile. Please try again."
            })

    return render(request, 'edit_profile.html', {
        "user": user,
        "profile_picture_url": profile_picture_url
    })


def upload_profile_picture(request):
    """Handle profile picture upload to Supabase storage bucket"""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method"}, status=400)
    
    if 'profile_picture' not in request.FILES:
        return JsonResponse({"success": False, "message": "No file provided"}, status=400)
    
    file = request.FILES['profile_picture']
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in allowed_extensions:
        return JsonResponse({
            "success": False, 
            "message": "Invalid file type. Please upload an image (JPG, PNG, GIF, or WEBP)"
        }, status=400)
    
    # Validate file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        return JsonResponse({
            "success": False, 
            "message": "File too large. Maximum size is 5MB"
        }, status=400)
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Generate unique filename
        unique_filename = f"{request.user.id}_{uuid.uuid4()}{file_ext}"
        
        # Read file content
        file_content = file.read()
        
        # Upload to Supabase storage bucket
        response = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(unique_filename)
        
        # Update or create user profile with the new profile picture URL
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Delete old profile picture from Supabase if exists
        if profile.profile_picture_url:
            try:
                # Extract filename from old URL
                old_filename = profile.profile_picture_url.split('/')[-1]
                supabase.storage.from_(settings.SUPABASE_BUCKET).remove([old_filename])
            except Exception as e:
                print(f"Error deleting old profile picture: {e}")
        
        profile.profile_picture_url = public_url
        profile.save()
        
        return JsonResponse({
            "success": True,
            "message": "Profile picture uploaded successfully!",
            "url": public_url
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Upload failed: {str(e)}"
        }, status=500)


def update_bio(request):
    """Handle bio update via AJAX POST request"""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method"}, status=400)
    
    import json
    try:
        data = json.loads(request.body)
        bio_text = data.get('bio', '').strip()
        
        # Validate bio length
        if len(bio_text) > 500:
            return JsonResponse({
                "success": False,
                "message": "Bio is too long. Maximum 500 characters allowed."
            }, status=400)
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.bio = bio_text if bio_text else None
        profile.save()
        
        return JsonResponse({
            "success": True,
            "message": "Bio updated successfully!",
            "bio": profile.bio
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Update failed: {str(e)}"
        }, status=500)
