from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Purchase(models.Model):
    """Purchase model to track book purchases"""
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    book_title = models.CharField(max_length=255)
    book_author = models.CharField(max_length=255, blank=True, null=True)
    book_cover_url = models.URLField(blank=True, null=True)
    olid = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment details (mock data)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    card_last_four = models.CharField(max_length=4)  # Last 4 digits of card
    cardholder_name = models.CharField(max_length=255)
    
    # Billing address
    billing_address = models.CharField(max_length=500)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_zip = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Transaction details
    transaction_id = models.CharField(max_length=50, unique=True)
    purchased_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.book_title} - {self.user.username} - {self.transaction_id}"
