# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Subject


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type')


class CustomUserChangeForm(UserChangeForm):
    """Form for editing users"""
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # What shows in user list
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_active']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Fields when EDITING existing user
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('User Type & Academic', {
            'fields': ('user_type', 'student_id', 'department')
        }),
        ('Face Recognition', {
            'fields': ('profile_image', 'reference_image'),
            'classes': ('collapse',),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )
    
    # Fields when ADDING new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'user_type'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin for Subject model"""
    list_display = ['name', 'code', 'staff', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']