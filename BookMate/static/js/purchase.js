// Purchase Modal Functions
let currentBookData = null;

// Simple notification function (fallback if module not loaded)
function showNotification(message, type = 'success') {
    // Try to use the module version if available
    if (window.showNotification) {
        window.showNotification(message, type);
        return;
    }
    
    // Fallback: simple alert-style notification
    const notification = document.createElement('div');
    notification.className = `simple-notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 2rem;
        background: ${type === 'success' ? '#50C878' : '#E74C3C'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        font-weight: 600;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Generate random price between $9.99 and $49.99
function generateBookPrice() {
    const min = 9.99;
    const max = 49.99;
    const price = (Math.random() * (max - min) + min).toFixed(2);
    return price;
}

// Open purchase modal with book details
function openPurchaseModal(bookData) {
    currentBookData = bookData;
    
    const modal = document.getElementById('purchaseModal');
    const purchaseForm = document.getElementById('purchaseForm');
    const submitBtn = purchaseForm.querySelector('.btn-purchase');
    const price = generateBookPrice();
    
    // Reset button state before opening
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('processing');
        submitBtn.innerHTML = 'Complete Purchase';
    }
    
    // Reset form
    purchaseForm.reset();
    
    // Remove old price input if exists
    const oldPriceInput = document.getElementById('bookPrice');
    if (oldPriceInput) {
        oldPriceInput.remove();
    }
    
    // Populate book details
    document.getElementById('purchaseBookCover').src = bookData.cover_url || '/static/images/default-book-cover.png';
    document.getElementById('purchaseBookTitle').textContent = bookData.title;
    document.getElementById('purchaseBookAuthor').textContent = `by ${bookData.author || 'Unknown Author'}`;
    document.getElementById('purchaseBookPrice').textContent = `$${price}`;
    
    // Set hidden fields
    document.getElementById('purchaseBookId').value = bookData.id || '';
    document.getElementById('purchaseBookOlid').value = bookData.olid || '';
    
    // Store price in form
    const priceInput = document.createElement('input');
    priceInput.type = 'hidden';
    priceInput.name = 'price';
    priceInput.id = 'bookPrice';
    priceInput.value = price;
    purchaseForm.appendChild(priceInput);
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Close purchase modal
function closePurchaseModal() {
    const modal = document.getElementById('purchaseModal');
    const purchaseForm = document.getElementById('purchaseForm');
    const submitBtn = purchaseForm.querySelector('.btn-purchase');
    
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Reset form
    purchaseForm.reset();
    
    // Reset button state
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('processing');
        submitBtn.innerHTML = '<span class="btn-icon">💰</span> Complete Purchase';
    }
    
    currentBookData = null;
    
    // Remove price input if exists
    const priceInput = document.getElementById('bookPrice');
    if (priceInput) {
        priceInput.remove();
    }
}

// Format card number input
document.addEventListener('DOMContentLoaded', function() {
    const cardNumberInput = document.getElementById('cardNumber');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
            e.target.value = formattedValue;
        });
    }
    
    // Format expiry date
    const expiryInput = document.getElementById('expiryDate');
    if (expiryInput) {
        expiryInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }
    
    // Only allow numbers in CVV
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }
});

// Handle purchase form submission
document.addEventListener('DOMContentLoaded', function() {
    const purchaseForm = document.getElementById('purchaseForm');
    if (purchaseForm) {
        purchaseForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = purchaseForm.querySelector('.btn-purchase');
            const originalText = submitBtn.innerHTML;
            
            // Show processing state
            submitBtn.disabled = true;
            submitBtn.classList.add('processing');
            submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Processing...';
            
            try {
                const formData = new FormData(purchaseForm);
                
                // Debug: Log what we're sending
                console.log('Sending purchase request to:', '/library/purchase/');
                console.log('Form data entries:', Array.from(formData.entries()));
                
                const response = await fetch('/library/purchase/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // Show success notification
                    showNotification('Purchase successful! Redirecting to dashboard...', 'success');
                    
                    // Close modal
                    closePurchaseModal();
                    
                    // Redirect to dashboard after 1.5 seconds
                    setTimeout(() => {
                        window.location.href = '/library/dashboard/';
                    }, 1500);
                } else {
                    showNotification(data.message || 'Purchase failed. Please try again.', 'error');
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('processing');
                    submitBtn.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Purchase error:', error);
                showNotification('An error occurred. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.classList.remove('processing');
                submitBtn.innerHTML = originalText;
            }
        });
    }
});

// Helper function to get CSRF token
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

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('purchaseModal');
    if (event.target === modal) {
        closePurchaseModal();
    }
});
