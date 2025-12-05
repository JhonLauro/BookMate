from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """User Profile model to store favorite genres and profile picture"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    favorite_genres = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Comma-separated favorite genres selected during registration"
    )
    profile_picture_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL to profile picture stored in Supabase bucket"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="User bio/description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_favorite_genres_list(self):
        """Returns favorite genres as a list"""
        if self.favorite_genres:
            return [g.strip() for g in self.favorite_genres.split(',') if g.strip()]
        return []
