from django.db import models
from django.contrib.auth.models import User


# User book list model
class UserBookList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_list')
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    pages = models.IntegerField(null=True, blank=True)
    cover_url = models.URLField(blank=True, null=True)
    olid = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True, null=True)
    is_favorite = models.BooleanField(default=False)
    current_page = models.IntegerField(default=0)
    tags = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Comma-separated custom tags (e.g., 'School, Romance, Adventure')"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'olid'], name='unique_user_book')
        ]
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author or 'Unknown'}"
    
    def get_tags_list(self):
        """Returns tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_list(self, tags_list):
        """Sets tags from a list"""
        self.tags = ", ".join(tags_list) if tags_list else ""
