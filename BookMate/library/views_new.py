from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserBookList
from profile_page.models import UserProfile
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from time import time
import requests
import json


def dashboard_view(request):
    """Display user dashboard with their books and recommendations"""
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


def search_books(request):
    """Search for books via Open Library API"""
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
            # Try Books API jscmd=data (best source)
            try:
                api_url = f"https://openlibrary.org/api/books?bibkeys=OLID:{olid}&jscmd=data&format=json"
                api_resp = requests.get(api_url)
                api_data = api_resp.json().get(f"OLID:{olid}", {})
                number_of_pages = api_data.get("number_of_pages")
            except Exception:
                pass

            # Edition fallback if still none
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
            "pages": number_of_pages or 0,
        })

    return JsonResponse({"results": results})


@csrf_exempt
def add_book(request):
    """Add a book to user's library"""
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

        pages = data.get("pages")

        # If pages not provided, fetch from Open Library
        if not pages:
            pages = None

            # Try jscmd=data API
            try:
                api_url = f"https://openlibrary.org/api/books?bibkeys=OLID:{olid}&jscmd=data&format=json"
                api_resp = requests.get(api_url)
                api_data = api_resp.json().get(f"OLID:{olid}", {})
                pages = api_data.get("number_of_pages")
            except Exception:
                pass

            # Try edition JSON fallback
            if not pages:
                try:
                    edition_url = f"https://openlibrary.org/books/{olid}.json"
                    edition_resp = requests.get(edition_url)
                    edition_data = edition_resp.json()
                    pages = edition_data.get("number_of_pages")

                    if not pages and edition_data.get("pagination"):
                        import re
                        digits = re.findall(r"\d+", edition_data["pagination"])
                        if digits:
                            pages = int(digits[-1])
                except Exception:
                    pages = None

        # Create or get book
        book, created = UserBookList.objects.get_or_create(
            user=request.user,
            olid=olid,
            defaults={
                "title": title,
                "author": author,
                "cover_url": cover_url,
                "pages": pages or 0,
            },
        )

        if not created:
            return JsonResponse({"message": "Book already in your list!"})

        return JsonResponse({"message": "Book added successfully!"})


@csrf_exempt
def remove_book(request):
    """Remove a book from user's library"""
    if request.method == "POST":
        data = json.loads(request.body)
        olid = data.get("olid")

        if not olid:
            return JsonResponse({"error": "No OLID provided"}, status=400)

        deleted_count, _ = UserBookList.objects.filter(user=request.user, olid=olid).delete()

        if deleted_count > 0:
            return JsonResponse({"message": "Book removed successfully!"})
        else:
            return JsonResponse({"message": "Book not found or already removed."}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def update_progress(request):
    """Update reading progress for a book"""
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


@csrf_exempt
def toggle_favorite(request):
    """Toggle favorite status for a book"""
    if request.method == "POST":
        data = json.loads(request.body)
        olid = data.get("olid")

        if not olid:
            return JsonResponse({"success": False, "message": "No OLID provided"}, status=400)

        try:
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


def book_preview(request, olid):
    """Display detailed book preview with caching"""
    # Check cache first
    cache_key = f"book_data_{olid}"
    cached_data = cache.get(cache_key)

    if cached_data:
        print(f"📘 Cache hit for {olid}")
        return render(request, "book_preview.html", cached_data)

    print(f"🌐 Cache miss for {olid}, fetching from API...")

    # Fetch from Open Library Works
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

    # Extract fields
    title = data.get("title", "Unknown Title")

    # Description
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

    # Authors
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

    # Cover
    cover_id = data.get("covers", [None])[0]
    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None

    if not cover_url:
        user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
        if user_book and user_book.cover_url:
            cover_url = user_book.cover_url

    # Pages fetching
    pages = None

    # Try Books API jscmd=data
    try:
        api_url = f"https://openlibrary.org/api/books?bibkeys=OLID:{olid}&jscmd=data&format=json"
        api_resp = requests.get(api_url)
        if api_resp.status_code == 200:
            api_data = api_resp.json().get(f"OLID:{olid}", {})
            pages = api_data.get("number_of_pages")
    except:
        pass

    # Try edition JSON fallback
    if not pages:
        try:
            edition_url = f"https://openlibrary.org/books/{olid}.json"
            edition_resp = requests.get(edition_url)
            if edition_resp.status_code == 200:
                edition_data = edition_resp.json()
                pages = edition_data.get("number_of_pages")

                if not pages and edition_data.get("pagination"):
                    import re
                    digits = re.findall(r"\d+", edition_data["pagination"])
                    if digits:
                        pages = int(digits[-1])
        except:
            pass

    # DB fallback
    if not pages:
        user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
        pages = user_book.pages if user_book else 0

    # Get user's book tags if they have this book
    user_book = UserBookList.objects.filter(user=request.user, olid=olid).first()
    book_tags = user_book.get_tags_list() if user_book else []

    # Prepare context
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


@csrf_exempt
def update_tags(request):
    """Update tags for a book"""
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Not logged in"}, status=403)
        
        data = json.loads(request.body)
        olid = data.get("olid")
        tags = data.get("tags", [])
        
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


def get_user_tags(request):
    """Get all unique tags from user's books for autocomplete"""
    if not request.user.is_authenticated:
        return JsonResponse({"tags": []})
    
    user_books = UserBookList.objects.filter(user=request.user)
    all_tags = set()
    
    for book in user_books:
        if book.tags:
            all_tags.update(book.get_tags_list())
    
    return JsonResponse({"tags": sorted(all_tags)})


def get_mock_book(request):
    """Return mock book data for testing reader"""
    return JsonResponse({
        "title": "The Chronicles of Random Thought",
        "pdf_url": "https://krigeshohndypdhbvijn.supabase.co/storage/v1/object/public/books/mock_book_400_pages.pdf?v=" + str(int(time()))
    })


def reader_view(request):
    """Display book reader page"""
    return render(request, "reader.html")
