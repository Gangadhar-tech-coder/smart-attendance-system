# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subject
from .forms import CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = User

    # Show these columns in the list view
    list_display = ('username', 'email', 'user_type', 'student_id', 'department')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Academic Info', {'fields': ('student_id', 'department')}),
        # Add the Profile Image field here so you can upload it
        ('Face Data', {'fields': ('profile_image',)}), 
        ('Reference Data',{'fields': ('reference_image',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type')}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'staff', 'created_at')