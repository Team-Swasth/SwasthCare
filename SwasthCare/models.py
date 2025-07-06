from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from django.contrib import admin

class UserProfile(models.Model):
    USER_TYPES = [
        ('seller', 'Seller'),
        ('consumer', 'Consumer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='consumer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}" # type: ignore
    
    @property
    def is_seller(self):
        return self.user_type == 'seller'
    
    @property
    def is_consumer(self):
        return self.user_type == 'consumer'

# Signal to automatically create user profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_type = 'seller' if instance.is_superuser else 'consumer'
        UserProfile.objects.create(user=instance, user_type=user_type)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# Admin registration for UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'created_at', 'updated_at')
    list_filter = ('user_type',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    # user_type is editable by default
