# apps/accounts/views.py - COMPLETE VERSION

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.middleware.csrf import get_token
from django.utils import timezone

from .models import User
from apps.attendance.models import AttendanceSession, AttendanceRecord
from django.core.files.base import ContentFile
import base64
from .forms import CustomUserCreationForm
from academics.models import Subject
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        
        live_image_data = request.POST.get('profile_image_data')

        if form.is_valid():
            user = form.save(commit=False)
            
            # Auto-assign student role since this page is students-only
            user.user_type = 'student'

            # Handle live camera capture
            if live_image_data:
                try:
                    format, imgstr = live_image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    file_data = ContentFile(base64.b64decode(imgstr), name=f'{user.username}_security.{ext}')
                    
                    if hasattr(user, 'reference_image'):
                        user.reference_image = file_data
                    else:
                        user.profile_image = file_data
                        
                except Exception as e:
                    print(f"Error saving image: {e}")

            user.save()
            login(request, user)
            
            # Pass success flag to trigger popup instead of redirecting immediately
            return render(request, 'signup.html', {
                'form': CustomUserCreationForm(),  # Fresh form
                'registration_success': True
            })
            
        else:
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


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.utils import timezone
from .decorators import role_required
from academics.models import Subject
from apps.attendance.models import AttendanceSession, AttendanceRecord

@login_required
def dashboard_redirect(request):
    """
    The main entry point: routes users to the correct URL based on role.
    """
    if request.user.user_type == 'student':
        return redirect('student_dashboard')
    elif request.user.user_type == 'staff' or request.user.user_type == 'hod':
        return redirect('faculty_dashboard')
    elif request.user.is_superuser or request.user.user_type == 'admin':
        return redirect('/admin/')
    return redirect('home')

@login_required
@role_required(allowed_roles=['student'])
def student_dashboard(request):
    from datetime import timedelta
    import json
    
    user = request.user
    get_token(request)

    # FIXED: subject_allocation__subject instead of subject
    active_sessions = AttendanceSession.objects.filter(
        is_active=True
    ).select_related(
        'subject_allocation__subject',
        'teacher'
    ).order_by('-start_time')

    marked_session_ids = AttendanceRecord.objects.filter(
        student=user,
        session__in=active_sessions
    ).values_list('session_id', flat=True)

    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # FIXED: session__subject_allocation__subject instead of session__subject
    attendance_history = AttendanceRecord.objects.filter(
        student=user,
        timestamp__gte=thirty_days_ago
    ).select_related(
        'session__subject_allocation__subject',
        'session__teacher'
    ).order_by('-timestamp')[:20]

    all_attendance = AttendanceRecord.objects.filter(
        student=user
    ).values('timestamp__date', 'status')

    attendance_calendar = {
        record['timestamp__date'].strftime('%Y-%m-%d'): record['status']
        for record in all_attendance
    }

    return render(request, 'student_dashboard.html', {
        'active_sessions': active_sessions,
        'marked_session_ids': list(marked_session_ids),
        'attendance_history': attendance_history,
        'attendance_calendar': json.dumps(attendance_calendar),
    })
@login_required
@role_required(allowed_roles=['staff', 'hod'])
def faculty_dashboard(request):
    user = request.user
    
    # Reach through Subject -> SubjectAllocation -> FacultyProfile -> User
    subjects = Subject.objects.filter(
        allocations__faculty__user=user, 
        allocations__is_active=True
    ).distinct()
    
    # ... rest of the view ...
    
    active_sessions = AttendanceSession.objects.filter(
        teacher=user,
        is_active=True
    ).select_related('subject_allocation__subject')

    recent_sessions = AttendanceSession.objects.filter(
        teacher=user
    ).select_related('subject_allocation__subject').order_by('-start_time')[:10]

    return render(request, 'staff_dashboard.html', {
        'subjects': subjects,
        'active_sessions': active_sessions,
        'active_sessions_count': active_sessions.count(),
        'recent_sessions': recent_sessions,
    })