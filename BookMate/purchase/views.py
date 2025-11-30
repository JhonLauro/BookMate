from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Purchase
from library.models import UserBookList
from decimal import Decimal
import requests
import secrets


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


def purchase_book(request):
    """Handle book purchase transactions"""
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


def get_purchase_history(request):
    """Get user's purchase history"""
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
