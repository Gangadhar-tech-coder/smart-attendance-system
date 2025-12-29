# apps/accounts/views.py - COMPLETE VERSION

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.middleware.csrf import get_token

from .models import User, Subject
from apps.attendance.models import AttendanceSession, AttendanceRecord


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
    """Login view for all user types"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    """
    Main dashboard - routes to appropriate dashboard based on user type
    """
    user = request.user
    
    # Ensure CSRF token
    get_token(request)
    
    # === STUDENT DASHBOARD ===
    if user.user_type == 'student':
        # Get active sessions
        active_sessions = AttendanceSession.objects.filter(
            is_active=True
        ).select_related('subject', 'teacher').order_by('-start_time')
        
        # Get sessions where student already marked attendance
        marked_session_ids = AttendanceRecord.objects.filter(
            student=user,
            session__in=active_sessions
        ).values_list('session_id', flat=True)
        
        return render(request, 'student_dashboard.html', {
            'user': user,
            'active_sessions': active_sessions,
            'marked_session_ids': list(marked_session_ids),
        })
    
    # === FACULTY DASHBOARD ===
    elif user.user_type == 'staff':
        # Get faculty's subjects
        subjects = Subject.objects.filter(staff=user)
        
        # Get active sessions
        active_sessions = AttendanceSession.objects.filter(
            teacher=user,
            is_active=True
        ).select_related('subject')
        
        # Get recent sessions (last 5)
        recent_sessions = AttendanceSession.objects.filter(
            teacher=user
        ).select_related('subject').order_by('-start_time')[:10]
        
        return render(request, 'staff_dashboard.html', {
            'user': user,
            'subjects': subjects,
            'active_sessions': active_sessions,
            'active_sessions_count': active_sessions.count(),
            'recent_sessions': recent_sessions,
        })
    
    # === ADMIN ===
    elif user.is_superuser or user.user_type == 'admin':
        return redirect('/admin/')
    
    # Fallback
    return redirect('home')