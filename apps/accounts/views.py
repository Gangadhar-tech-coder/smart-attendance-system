from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.contrib import messages
import base64

from .forms import CustomUserCreationForm

# --- CRITICAL CHANGE 1: Import the AttendanceSession model ---
from apps.attendance.models import AttendanceSession 
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.files.base import ContentFile
import base64
from .forms import CustomUserCreationForm

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES) # Note: Added request.FILES
        
        # 1. Get the Live Camera Data (Base64 string from hidden input)
        live_image_data = request.POST.get('profile_image_data')

        if form.is_valid():
            user = form.save(commit=False)

            # 2. HANDLE LIVE CAMERA CAPTURE (Security Reference)
            if live_image_data:
                try:
                    format, imgstr = live_image_data.split(';base64,') 
                    ext = format.split('/')[-1] 
                    # Create a file object from the string
                    file_data = ContentFile(base64.b64decode(imgstr), name=f'{user.username}_security.{ext}')
                    
                    # Save to the 'reference_image' field (Used for Face ID)
                    # If your model doesn't have 'reference_image', change this to 'profile_image'
                    if hasattr(user, 'reference_image'):
                        user.reference_image = file_data
                    else:
                        user.profile_image = file_data # Fallback
                        
                except Exception as e:
                    print(f"Error saving image: {e}")

            # 3. Save User & Login
            user.save()
            login(request, user)
            return redirect('dashboard')
            
        else:
            # --- CRITICAL: Print errors to terminal so you know WHY it failed ---
            print("❌ SIGNUP FAILED. Form Errors:")
            print(form.errors)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    
    if user.user_type == 'student':
        # --- CRITICAL CHANGE 2: Fetch Active Sessions from DB ---
        active_sessions = AttendanceSession.objects.filter(is_active=True)
        
        # Pass 'active_sessions' to the template
        return render(request, 'student_dashboard.html', {
            'user': user, 
            'active_sessions': active_sessions
        })
        
    elif user.user_type == 'staff':
        return render(request, 'staff_dashboard.html', {'user': user})
        
    elif user.is_superuser:
        return redirect('/admin/') 
        
    return redirect('home')