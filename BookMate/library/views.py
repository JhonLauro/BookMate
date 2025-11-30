from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserBookList
from profile_page.models import UserProfile
from purchase.models import Purchase
from django.core.cache import cache
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import F
from django.conf import settings
from time import time
import requests
import json


# Dashboard view (moved from below)

def register_view(request):
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data["password1"])
                user.save()
                messages.success(request, "Registration successful! Please sign in to continue.")
                return redirect(f"{reverse('landing')}?modal=login")
            except IntegrityError:
                # Username or email already exists
                request.session['register_errors'] = {
                    'general': ['Invalid credentials. Please check your information and try again.']
                }
                return redirect(f"{reverse('landing')}?modal=register")
            
        else:
            # Generic error message for security and formality
            request.session['register_errors'] = {'general': ['Invalid credentials. Please check your information and try again.']}
            return redirect(f"{reverse('landing')}?modal=register")
    else:
        # Redirect GET requests to landing page
        return redirect("landing")

#login function
def login_view(request):
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Validate credentials
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
        else:
            # Generic error message for security
            request.session['login_errors'] = {'general': ['Invalid credentials. Please try again.']}
            # Save username to repopulate the form
            request.session['login_username'] = username
            return redirect(f"{reverse('landing')}?modal=login")
    else:
        # Redirect GET requests to landing page
        return redirect("landing")

def logout_view(request):
    logout(request)
    # Removed notification - landing page already shows logout message
    return redirect("landing")

def landing_view(request):
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Get form errors from session if they exist
    register_errors = request.session.pop('register_errors', {})
    login_errors = request.session.pop('login_errors', {})
    login_username = request.session.pop('login_username', '')
    open_modal = request.GET.get('modal', '')
    
    return render(request, 'landing.html', {
        'register_errors': register_errors,
        'login_errors': login_errors,
        'login_username': login_username,
        'open_modal': open_modal,
    })

def genre_setup_view(request):
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

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch this user's saved books
    user_books = UserBookList.objects.filter(user=request.user).order_by('title')
    
    # Initialize variables
    recommended_books = []
    user_favorite_genres = []
    user_tags = set()
    
    # Collect all unique tags from user's books
    for book in user_books:
        if book.tags:
            user_tags.update(book.get_tags_list())
    
    # Get user's profile with favorite genres
    profile = None
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.favorite_genres:
            user_favorite_genres = profile.get_favorite_genres_list()
    except UserProfile.DoesNotExist:
        pass
    
    # Build search terms from genres and tags
    search_terms = []
    if user_favorite_genres:
        search_terms.extend(user_favorite_genres[:3])
    if user_tags:
        search_terms.extend(list(user_tags)[:2])
    
    # Fetch recommendations if we have search terms
    if search_terms:
        try:
            query = "+".join(search_terms)  # Use + for better search
            url = f"https://openlibrary.org/search.json?q={query}&limit=20"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                user_olids = set(user_books.values_list('olid', flat=True))
                
                for book in data.get("docs", []):
                    if len(recommended_books) >= 12:
                        break
                    
                    # Get OLID
                    olid = book.get("cover_edition_key")
                    if not olid and book.get("edition_key"):
                        olid = book.get("edition_key")[0]
                    
                    # Skip if no OLID or user already has it
                    if not olid or olid in user_olids:
                        continue
                    
                    # Add to recommendations
                    recommended_books.append({
                        "title": book.get("title", "Unknown Title"),
                        "author": ", ".join(book.get("author_name", [])) if book.get("author_name") else "Unknown",
                        "cover_url": f"https://covers.openlibrary.org/b/olid/{olid}-M.jpg",
                        "olid": olid,
                        "year": book.get("first_publish_year", "Unknown"),
                    })
        except Exception as e:
            print(f"Error fetching recommendations: {e}")
    
    return render(request, "dashboard.html", {
        "user_books": user_books,
        "recommended_books": recommended_books,
        "user_favorite_genres": user_favorite_genres,
        "user_tags": sorted(list(user_tags)),
    })



def profile_view(request):
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
    try:
        profile = UserProfile.objects.get(user=user)
        user_favorite_genres = profile.get_favorite_genres_list()
        profile_picture_url = profile.profile_picture_url
    except UserProfile.DoesNotExist:
        user_favorite_genres = []
        profile_picture_url = None
    
    context = {
        'user': user,
        'total_books': total_books,
        'currently_reading': books_with_progress.count(),
        'finished_books': finished_books.count(),
        'favorite_books_count': favorite_books.count(),
        'user_favorite_genres': user_favorite_genres,
        'profile_picture_url': profile_picture_url,
        'reading_books': books_with_progress[:100],  # Show 100 currently reading
        'completed_books': finished_books[:100],  # Show 100 finished
        'favorite_books': favorite_books[:100],  # Show 100 favorite books
    }
    
    return render(request, 'profile.html', context)


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


def buy_book_links(request, olid):
    """Display buy links for a book - Philippine stores first, then international"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get book details
    book = UserBookList.objects.filter(user=request.user, olid=olid).first()
    
    if book:
        title = book.title
        author = book.author or "Unknown"
        cover_url = book.cover_url
    else:
        # If user doesn't have the book, try to get info from the page context
        title = request.GET.get('title', 'Book')
        author = request.GET.get('author', 'Unknown')
        cover_url = request.GET.get('cover', '')
    
    # Build search query
    search_query = f"{title} {author}".strip()
    
    # Philippine bookstores (prioritized)
    ph_bookstores = [
        {
            "name": "Fully Booked",
            "url": f"https://www.fullybookedonline.com/search?q={search_query}",
            "description": "Philippines' largest bookstore chain",
            "currency": "PHP"
        },
        {
            "name": "National Book Store",
            "url": f"https://www.nationalbookstore.com/search?q={search_query}",
            "description": "Trusted Philippine bookstore since 1942",
            "currency": "PHP"
        },
        {
            "name": "Book Sale",
            "url": f"https://www.booksale.com.ph/search?q={search_query}",
            "description": "Affordable books in the Philippines",
            "currency": "PHP"
        },
    ]
    
    # International bookstores (fallback)
    international_bookstores = [
        {
            "name": "Amazon",
            "url": f"https://www.amazon.com/s?k={search_query}",
            "description": "Global online retailer",
            "currency": "USD"
        },
        {
            "name": "Book Depository",
            "url": f"https://www.bookdepository.com/search?searchTerm={search_query}",
            "description": "Free worldwide delivery",
            "currency": "USD"
        },
        {
            "name": "AbeBooks",
            "url": f"https://www.abebooks.com/servlet/SearchResults?kn={search_query}",
            "description": "New, used, and rare books",
            "currency": "USD"
        },
    ]
    
    context = {
        'book': book,
        'title': title,
        'author': author,
        'cover_url': cover_url,
        'olid': olid,
        'ph_bookstores': ph_bookstores,
        'international_bookstores': international_bookstores,
    }
    
    return render(request, 'buy_book_links.html', context)


def edit_profile_view(request):
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

        # Update basic info
        user.username = username
        user.email = email

        # Handle password update (optional)
        if password1 and password1 == password2:
            user.set_password(password1)
            user.save()
            # Re-authenticate the user after password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, "✅ Profile updated successfully! Password changed.")
        elif password1 or password2:
            messages.error(request, "⚠️ Passwords do not match!")
            # Refresh profile picture URL before re-rendering
            try:
                profile = UserProfile.objects.get(user=user)
                profile_picture_url = profile.profile_picture_url
            except UserProfile.DoesNotExist:
                profile_picture_url = None
            return render(request, 'edit_profile.html', {
                "user": user,
                "profile_picture_url": profile_picture_url
            })

        user.save()
        messages.success(request, "✅ Profile updated successfully!")
        return redirect('profile')

    return render(request, 'edit_profile.html', {
        "user": user,
        "profile_picture_url": profile_picture_url
    })



#api functionalities
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# --- SEARCH BOOKS via Open Library API ---
def search_books(request):
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"results": []})

    url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(url)
    data = response.json()

    results = []
    for book in data.get("docs", [])[:10]:
        olid = book.get("cover_edition_key") or (
            book.get("edition_key")[0] if book.get("edition_key") else None
        )
        cover_url = f"https://covers.openlibrary.org/b/olid/{olid}-M.jpg" if olid else None

        number_of_pages = None

        if olid:
            # ✅ 1) Try Books API jscmd=data (best source)
            try:
                api_url = f"https://openlibrary.org/api/books?bibkeys=OLID:{olid}&jscmd=data&format=json"
                api_resp = requests.get(api_url)
                api_data = api_resp.json().get(f"OLID:{olid}", {})

                number_of_pages = api_data.get("number_of_pages")
            except Exception:
                pass

            # ✅ 2) Edition fallback if still none
            if not number_of_pages:
                try:
                    edition_url = f"https://openlibrary.org/books/{olid}.json"
                    edition_resp = requests.get(edition_url)
                    edition_data = edition_resp.json()

                    number_of_pages = edition_data.get("number_of_pages")

                    # Fallback: parse from pagination text
                    if not number_of_pages and edition_data.get("pagination"):
                        import re
                        digits = re.findall(r"\d+", edition_data["pagination"])
                        if digits:
                            number_of_pages = int(digits[-1])
                except Exception:
                    number_of_pages = None

        results.append({
            "title": book.get("title"),
            "author": ", ".join(book.get("author_name", [])) if book.get("author_name") else "Unknown",
            "cover_url": cover_url,
            "olid": olid,
            "pages": number_of_pages or 0,  # ✅ always return a number
        })

    return JsonResponse({"results": results})


# --- ADD BOOK TO USER LIST ---
@csrf_exempt
def add_book(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"message": "You must be logged in to add books."}, status=403)

        data = json.loads(request.body)
        title = data.get("title")
        author = data.get("author")
        cover_url = data.get("cover_url")
        olid = data.get("olid")

        if not olid:
            return JsonResponse({"message": "Missing book ID (OLID)."}, status=400)

        pages = data.get("pages")  # may be None from frontend

        # ✅ If pages not provided by search API, fetch from Open Library
        if not pages:
            pages = None

            # 1) Try jscmd=data API
            try:
                api_url = f"https://openlibrary.org/api/books?bibkeys=OLID:{olid}&jscmd=data&format=json"
                api_resp = requests.get(api_url)
                api_data = api_resp.json().get(f"OLID:{olid}", {})

                pages = api_data.get("number_of_pages")
            except Exception:
                pass

            # 2) Try edition JSON fallback
            if not pages:
                try:
                    edition_url = f"https://openlibrary.org/books/{olid}.json"
                    edition_resp = requests.get(edition_url)
                    edition_data = edition_resp.json()

                    pages = edition_data.get("number_of_pages")

                    # parse pagination if needed
                    if not pages and edition_data.get("pagination"):
                        import re
                        digits = re.findall(r"\d+", edition_data["pagination"])
                        if digits:
                            pages = int(digits[-1])
                except Exception:
                    pages = None

        # ✅ Create or get book
        book, created = UserBookList.objects.get_or_create(
            user=request.user,
            olid=olid,
            defaults={
                "title": title,
                "author": author,
                "cover_url": cover_url,
                "pages": pages or 0,  # always store something
            },
        )

        if not created:
            return JsonResponse({"message": "Book already in your list!"})

        return JsonResponse({"message": "Book added successfully!"})

# --- REMOVE BOOK FROM USER LIST ---
@csrf_exempt
def remove_book(request):
    if request.method == "POST":
        data = json.loads(request.body)
        olid = data.get("olid")

        if not olid:
            return JsonResponse({"error": "No OLID provided"}, status=400)

        # Delete the book belonging to this user
        deleted_count, _ = UserBookList.objects.filter(user=request.user, olid=olid).delete()

        if deleted_count > 0:
            return JsonResponse({"message": "Book removed successfully!"})
        else:
            return JsonResponse({"message": "Book not found or already removed."}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)


# --- EDIT BOOK DETAILS ---
@csrf_exempt
def update_progress(request):
    if request.method == "POST":
        data = json.loads(request.body)
        olid = data.get("olid")
        progress = data.get("progress")

        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Not logged in"}, status=403)

        try:
            book = UserBookList.objects.get(user=request.user, olid=olid)
            book.current_page = int(progress)
            book.save()
            return JsonResponse({"success": True, "progress": book.current_page})
        except UserBookList.DoesNotExist:
            return JsonResponse({"success": False, "message": "Book not found"}, status=404)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

#Toggle
@csrf_exempt
def toggle_favorite(request):
    if request.method == "POST":
        data = json.loads(request.body)
        olid = data.get("olid")

        if not olid:
            return JsonResponse({"success": False, "message": "No OLID provided"}, status=400)

        try:
            # Toggle favorite status for the book belonging to this user
            book = UserBookList.objects.get(user=request.user, olid=olid)
            book.is_favorite = not book.is_favorite
            book.save()

            return JsonResponse({
                "success": True,
                "message": f"Book {'marked' if book.is_favorite else 'unmarked'} as favorite!",
                "is_favorite": book.is_favorite
            })
        except UserBookList.DoesNotExist:
            return JsonResponse({"success": False, "message": "Book not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


#DIRECT TO BOOK PREVIEW
def dashboard(request):
    user_books = UserBookList.objects.filter(user=request.user)
    return render(request, 'dashboard.html', {'user_books': user_books})


# --- UPDATE BOOK DETAILS (genres, tags, links) ---
@csrf_exempt
# def book_preview(request, olid):
#     book = get_object_or_404(UserBookList, olid=olid, user=request.user)
#     return render(request, 'book_preview.html', {'book': book})


#BOOK PREVIEW API FETCH
def book_preview(request, olid):
    # --- Check cache first ---
    cache_key = f"book_data_{olid}"
    cached_data = cache.get(cache_key)

    if cached_data:
        print(f"📘 Cache hit for {olid}")
        return render(request, "book_preview.html", cached_data)

    print(f"🌐 Cache miss for {olid}, fetching from API...")

    # --- Fetch from Open Library Works ---
    work_url = f"https://openlibrary.org/works/{olid}.json"
    work_response = requests.get(work_url)

    if work_response.status_code != 200:
        edition_url = f"https://openlibrary.org/books/{olid}.json"
        edition_response = requests.get(edition_url)
        if edition_response.status_code == 200:
            data = edition_response.json()
        else:
            user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
            data = {
                "title": user_book.title if user_book else "Book not found",
                "authors": [user_book.author] if user_book else [],
                "description": "No data available.",
                "cover_url": user_book.cover_url if user_book else None,
                "olid": olid,
                "pages": user_book.pages if user_book else 0,
            }
            cache.set(cache_key, data, timeout=3600)
            return render(request, "book_preview.html", data)
    else:
        data = work_response.json()

    # --- Extract fields ---
    title = data.get("title", "Unknown Title")

    # ✅ Description
    if "description" in data:
        description = data["description"]["value"] if isinstance(data["description"], dict) else data["description"]
    elif "excerpts" in data and data["excerpts"]:
        description = data["excerpts"][0].get("excerpt", "")
    elif "first_sentence" in data:
        description = data["first_sentence"].get("value", "") if isinstance(data["first_sentence"], dict) else data["first_sentence"]
    elif "notes" in data:
        description = data["notes"]
    else:
        description = "No description available."

    # ✅ Authors
    authors = []
    if "authors" in data:
        for author_obj in data["authors"]:
            key = author_obj.get("author", {}).get("key") or author_obj.get("key")
            if key:
                author_url = f"https://openlibrary.org{key}.json"
                author_res = requests.get(author_url)
                if author_res.status_code == 200:
                    author_data = author_res.json()
                    authors.append(author_data.get("name"))
    elif "by_statement" in data:
        authors.append(data["by_statement"])
    elif "author_name" in data:
        authors.append(", ".join(data["author_name"]))

    if not authors:
        user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
        authors = [user_book.author] if user_book and user_book.author else ["Unknown Author"]

    # ✅ Cover
    cover_id = data.get("covers", [None])[0]
    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None

    if not cover_url:
        user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
        if user_book and user_book.cover_url:
            cover_url = user_book.cover_url

    # ✅ ✅ ✅ PAGES FETCHING

    pages = None

    # 1) Try Books API jscmd=data (most reliable)
    try:
        api_url = f"https://openlibrary.org/api/books?bibkeys=OLID:{olid}&jscmd=data&format=json"
        api_resp = requests.get(api_url)
        if api_resp.status_code == 200:
            api_data = api_resp.json().get(f"OLID:{olid}", {})
            pages = api_data.get("number_of_pages")
    except:
        pass

    # 2) Try edition JSON (fallback)
    if not pages:
        try:
            edition_url = f"https://openlibrary.org/books/{olid}.json"
            edition_resp = requests.get(edition_url)
            if edition_resp.status_code == 200:
                edition_data = edition_resp.json()
                pages = edition_data.get("number_of_pages")

                # Fallback from pagination (e.g. "350 pages")
                if not pages and edition_data.get("pagination"):
                    import re
                    digits = re.findall(r"\d+", edition_data["pagination"])
                    if digits:
                        pages = int(digits[-1])
        except:
            pass

    # 3) DB fallback
    if not pages:
        user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
        pages = user_book.pages if user_book else 0

    # Get user's book tags if they have this book
    user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
    book_tags = user_book.get_tags_list() if user_book else []

    # ✅ Prepare context
    context = {
        "title": title,
        "authors": authors,
        "description": description,
        "cover_url": cover_url,
        "olid": olid,
        "pages": pages or 0,
        "book_tags": book_tags,
        "has_book": user_book is not None,
    }

    cache.set(cache_key, context, timeout=3600)
    return render(request, "book_preview.html", context)


# --- UPDATE BOOK TAGS ---
@csrf_exempt
def update_tags(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Not logged in"}, status=403)
        
        data = json.loads(request.body)
        olid = data.get("olid")
        tags = data.get("tags", [])  # Expecting a list of tags
        
        if not olid:
            return JsonResponse({"success": False, "message": "No OLID provided"}, status=400)
        
        try:
            book = UserBookList.objects.get(user=request.user, olid=olid)
            book.set_tags_list(tags)
            book.save()
            
            return JsonResponse({
                "success": True,
                "message": "Tags updated successfully!",
                "tags": book.get_tags_list()
            })
        except UserBookList.DoesNotExist:
            return JsonResponse({"success": False, "message": "Book not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


# --- GET USER'S ALL TAGS (for autocomplete)
def get_user_tags(request):
    if not request.user.is_authenticated:
        return JsonResponse({"tags": []})
    
    # Get all unique tags from user's books
    user_books = UserBookList.objects.filter(user=request.user)
    all_tags = set()
    
    for book in user_books:
        if book.tags:
            all_tags.update(book.get_tags_list())
    
    return JsonResponse({"tags": sorted(all_tags)})


# --- PURCHASE BOOK VIEW
def purchase_book(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Not logged in"}, status=403)
    
    if request.method == "POST":
        
        try:
            # Get form data
            olid = request.POST.get('olid')
            price = Decimal(request.POST.get('price', '0'))
            payment_method = request.POST.get('payment_method')
            card_number = request.POST.get('card_number', '').replace(' ', '')
            cardholder_name = request.POST.get('cardholder_name')
            expiry_date = request.POST.get('expiry_date')
            cvv = request.POST.get('cvv')
            billing_address = request.POST.get('billing_address')
            billing_city = request.POST.get('billing_city')
            billing_state = request.POST.get('billing_state')
            billing_zip = request.POST.get('billing_zip')
            billing_country = request.POST.get('billing_country')
            
            # Validate required fields
            if not all([olid, price, payment_method, card_number, cardholder_name, 
                       billing_address, billing_city, billing_state, billing_zip, billing_country]):
                return JsonResponse({"success": False, "message": "Missing required fields"}, status=400)
            
            # Get book details from Open Library API
            try:
                response = requests.get(f"https://openlibrary.org/works/{olid}.json", timeout=10)
                if response.status_code != 200:
                    return JsonResponse({"success": False, "message": "Book not found"}, status=404)
            except requests.RequestException as e:
                return JsonResponse({"success": False, "message": "Failed to fetch book details"}, status=500)
            
            book_data = response.json()
            title = book_data.get('title', 'Unknown Title')
            
            # Get author with better error handling
            author = 'Unknown Author'
            try:
                if 'authors' in book_data and book_data['authors']:
                    author_key = book_data['authors'][0].get('author', {}).get('key')
                    if author_key:
                        author_response = requests.get(f"https://openlibrary.org{author_key}.json", timeout=5)
                        if author_response.status_code == 200:
                            author = author_response.json().get('name', 'Unknown Author')
            except Exception as e:
                print(f"Error fetching author: {e}")
                author = 'Unknown Author'
            
            # Get cover
            cover_url = None
            if 'covers' in book_data and book_data['covers']:
                cover_id = book_data['covers'][0]
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            
            # Generate unique transaction ID
            transaction_id = f"TXN-{secrets.token_hex(8).upper()}"
            
            # Get last 4 digits of card
            card_last_four = card_number[-4:] if len(card_number) >= 4 else card_number
            
            # Create purchase record
            purchase = Purchase.objects.create(
                user=request.user,
                book_title=title,
                book_author=author,
                book_cover_url=cover_url,
                olid=olid,
                price=price,
                payment_method=payment_method,
                card_last_four=card_last_four,
                cardholder_name=cardholder_name,
                billing_address=billing_address,
                billing_city=billing_city,
                billing_state=billing_state,
                billing_zip=billing_zip,
                billing_country=billing_country,
                transaction_id=transaction_id
            )
            
            response = JsonResponse({
                "success": True,
                "message": "Purchase completed successfully!",
                "transaction_id": transaction_id,
                "book_title": title
            })
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
            
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)
    
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=400)


# --- GET USER PURCHASE HISTORY
def get_purchase_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Not logged in"}, status=403)
    
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchased_at')
    
    purchase_list = []
    for purchase in purchases:
        purchase_list.append({
            'id': purchase.id,
            'book_title': purchase.book_title,
            'book_author': purchase.book_author,
            'book_cover_url': purchase.book_cover_url,
            'price': str(purchase.price),
            'payment_method': purchase.get_payment_method_display(),
            'card_last_four': purchase.card_last_four,
            'transaction_id': purchase.transaction_id,
            'purchased_at': purchase.purchased_at.strftime('%B %d, %Y at %I:%M %p')
        })
    
    response = JsonResponse({"success": True, "purchases": purchase_list})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


# book
# views.py
from django.http import JsonResponse
from time import time


# loads book but always the newest version of book
def get_mock_book(request):
    return JsonResponse({
        "title": "The Chronicles of Random Thought",
        "pdf_url": "https://krigeshohndypdhbvijn.supabase.co/storage/v1/object/public/books/mock_book_400_pages.pdf?v=" + str(int(time()))
    })


def reader_view(request):
    return render(request, "reader.html")
