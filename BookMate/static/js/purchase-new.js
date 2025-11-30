// Purchase Modal Functions - Completely Rewritten
let currentBookData = null;

// Simple notification function
function showNotification(message, type = 'success') {
    if (window.showNotification) {
        window.showNotification(message, type);
        return;
    }
    
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 1rem 2rem;
        background: ${type === 'success' ? '#50C878' : '#E74C3C'};
        color: white; border-radius: 8px; z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-weight: 600;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Generate random price
function generateBookPrice() {
    return ((Math.random() * 40) + 9.99).toFixed(2);
}

// Open modal
function openPurchaseModal(bookData) {
    currentBookData = bookData;
    const modal = document.getElementById('purchaseModal');
    const form = document.getElementById('purchaseForm');
    const price = generateBookPrice();
    
    // Reset form and button
    form.reset();
    const submitBtn = form.querySelector('.btn-purchase');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('processing');
        submitBtn.innerHTML = '<span class="btn-icon">💰</span> Complete Purchase';
    }
    
    // Populate book info
    document.getElementById('purchaseBookCover').src = bookData.cover_url || '/static/images/default-book-cover.png';
    document.getElementById('purchaseBookTitle').textContent = bookData.title;
    document.getElementById('purchaseBookAuthor').textContent = `by ${bookData.author || 'Unknown Author'}`;
    document.getElementById('purchaseBookPrice').textContent = `$${price}`;
    document.getElementById('purchaseBookId').value = bookData.id || '';
    document.getElementById('purchaseBookOlid').value = bookData.olid || '';
    
    // Remove old price input if exists
    const oldPrice = document.getElementById('bookPrice');
    if (oldPrice) oldPrice.remove();
    
    // Add new price input
    const priceInput = document.createElement('input');
    priceInput.type = 'hidden';
    priceInput.name = 'price';
    priceInput.id = 'bookPrice';
    priceInput.value = price;
    form.appendChild(priceInput);
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Close modal
function closePurchaseModal() {
    const modal = document.getElementById('purchaseModal');
    const form = document.getElementById('purchaseForm');
    
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    form.reset();
    
    const submitBtn = form.querySelector('.btn-purchase');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('processing');
        submitBtn.innerHTML = '<span class="btn-icon">💰</span> Complete Purchase';
    }
    
    currentBookData = null;
    const priceInput = document.getElementById('bookPrice');
    if (priceInput) priceInput.remove();
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize form handlers
document.addEventListener('DOMContentLoaded', function() {
    // Card number formatting
    const cardNumber = document.getElementById('cardNumber');
    if (cardNumber) {
        cardNumber.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            e.target.value = value.match(/.{1,4}/g)?.join(' ') || value;
        });
    }
    
    // Expiry date formatting
    const expiry = document.getElementById('expiryDate');
    if (expiry) {
        expiry.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }
    
    // CVV - numbers only
    const cvv = document.getElementById('cvv');
    if (cvv) {
        cvv.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }
    
    // Form submission
    const form = document.getElementById('purchaseForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.querySelector('.btn-purchase');
            if (!submitBtn) {
                console.error('Submit button not found');
                return;
            }
            const originalText = submitBtn.innerHTML;
            
            submitBtn.disabled = true;
            submitBtn.classList.add('processing');
            submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Processing...';
            
            try {
                const formData = new FormData(form);
                
                console.log('Submitting to: /purchase/purchase/');
                console.log('Form data:', Object.fromEntries(formData));
                
                const response = await fetch('/purchase/purchase/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData
                });
                
                console.log('Response status:', response.status);
                const text = await response.text();
                console.log('Response text:', text);
                
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    console.error('Failed to parse JSON:', e);
                    showNotification('Server error. Please try again.', 'error');
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('processing');
                    submitBtn.innerHTML = originalText;
                    return;
                }
                
                if (response.ok && data.success) {
                    showNotification('Purchase successful! Redirecting...', 'success');
                    closePurchaseModal();
                    setTimeout(() => {
                        window.location.href = '/dashboard/';
                    }, 1500);
                } else {
                    showNotification(data.message || 'Purchase failed', 'error');
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('processing');
                    submitBtn.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Purchase error:', error);
                showNotification('An error occurred', 'error');
                submitBtn.disabled = false;
                submitBtn.classList.remove('processing');
                submitBtn.innerHTML = originalText;
            }
        });
    }
});

// Close on outside click
window.addEventListener('click', function(event) {
    const modal = document.getElementById('purchaseModal');
    if (event.target === modal) {
        closePurchaseModal();
    }
});
