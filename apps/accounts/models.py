# accounts/models.py
"""
Enhanced User and Subject models integrating PostgreSQL schema features
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator

class User(AbstractUser):
    """
    Custom User model combining your existing structure with PostgreSQL schema
    """
    # --- ROLES (Enhanced to include HOD) ---
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('hod', 'Head of Department'),  # NEW: Added HOD role
        ('staff', 'Staff/Faculty'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    
    # --- PERSONAL INFO ---
    phone_number = models.CharField(max_length=15, blank=True)
    
    # --- ACADEMIC INFO (For Students) ---
    student_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        unique=True, 
        help_text="Roll Number"
    )
    department = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="e.g. CSE, ECE"
    )

    # --- FACE RECOGNITION DATA (For Smart Attendance) ---
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        null=True, 
        blank=True
    )
    reference_image = models.ImageField(
        upload_to='security_references/', 
        blank=True, 
        null=True
    )
    face_encoding = models.BinaryField(null=True, blank=True)
    
    # --- NEW FIELDS FROM POSTGRESQL SCHEMA ---
    is_active = models.BooleanField(default=True)
    # Note: is_staff and is_superuser already exist in AbstractUser
    
    class Meta:
        db_table = 'users'  # Match PostgreSQL table name if desired
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['user_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.username


# --- SUBJECT MODEL (For Staff) ---
# Note: This is being kept for backward compatibility
# Consider migrating to academics.Subject instead
# class Subject(models.Model):
#     """
#     Legacy Subject model - Consider using academics.Subject instead
#     Keeping for backward compatibility
#     """
#     name = models.CharField(max_length=100)
#     code = models.CharField(max_length=20, unique=True)
    
#     staff = models.ForeignKey(
#         User, 
#         on_delete=models.CASCADE, 
#         limit_choices_to={'user_type__in': ['staff', 'hod']},  # Updated to include HOD
#         related_name='subjects'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"{self.name} ({self.code})"