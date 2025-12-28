from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        # Removed 'profile_image' from here. We will handle it in the view.
        fields = ('username', 'email', 'user_type', 'student_id', 'department')