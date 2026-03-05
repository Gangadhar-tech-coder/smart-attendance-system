from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    student_id = forms.CharField(max_length=20, required=False, empty_value=None, help_text="Roll Number")
    class Meta:
        model = User
        # Removed 'profile_image' from here. We will handle it in the view.
        fields = ('username', 'email', 'user_type', 'student_id', 'department')

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id:
            return None
        return student_id