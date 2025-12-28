# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # --- ROLES ---
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    
    # --- PERSONAL INFO ---
    phone_number = models.CharField(max_length=15, blank=True)
    
    # --- ACADEMIC INFO (For Students) ---
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True, help_text="Roll Number")
    department = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. CSE, ECE")

    # --- FACE RECOGNITION DATA (For Smart Attendance) ---
    # Stores the photo of the student
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    reference_image = models.ImageField(upload_to='security_references/', blank=True, null=True)
    # Stores the mathematical representation of the face for AI comparison
    face_encoding = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"

# --- SUBJECT MODEL (For Staff) ---
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    staff = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'staff'},
        related_name='subjects'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"