from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    # This controls the columns displayed in the user list view
    list_display = ("email", "username", "phone", "is_active", "is_staff", "created_at")
    
    # This adds a quick search bar at the top to search users by their info
    search_fields = ("email", "username", "phone")
    
    # This adds a sidebar on the right to easily filter by active or staff status
    list_filter = ("is_active", "is_staff")
