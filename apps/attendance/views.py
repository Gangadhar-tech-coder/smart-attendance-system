from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile

from .models import AttendanceSession, AttendanceRecord
from apps.accounts.models import Subject
from .utils import is_within_radius, check_face_match

# --- BASIC VIEWS ---
def home(request): return render(request, 'home.html')

@login_required
def select_class(request):
    subjects = Subject.objects.filter(staff=request.user)
    return render(request, 'select_class.html', {'subjects': subjects})

@login_required
def create_session(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Default Coordinates (Update these to your location!)
    session = AttendanceSession.objects.create(
        teacher=request.user, 
        subject=subject, 
        is_active=True,
        latitude=12.9716, 
        longitude=77.5946, 
        radius_meters=500
    )
    return redirect('monitor_session', session_id=session.id)

@login_required
def monitor_session(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    records = AttendanceRecord.objects.filter(session=session).order_by('-timestamp')
    return render(request, 'monitor_session.html', {'session': session, 'records': records})

@login_required
def end_session(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    session.is_active = False
    session.end_time = timezone.now()
    session.save()
    return redirect('dashboard')

# --- THE LOGIC YOU REQUESTED ---

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from .models import AttendanceSession, AttendanceRecord
from .utils import is_within_radius, check_face_match

from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AttendanceSession, AttendanceRecord
from .utils import is_within_radius, check_face_match

@csrf_exempt
def verify_my_face(request):
    if request.method != 'POST': 
        return JsonResponse({'error': 'Invalid Method'}, status=405)
    
    if not request.user.is_authenticated: 
        return JsonResponse({'error': 'Session expired. Please login.'}, status=401)

    try:
        # 1. Parse Data
        session_id = request.POST.get('session')
        lat = float(request.POST.get('gps_lat', 0))
        lng = float(request.POST.get('gps_long', 0))
        captured_file = request.FILES.get('captured_image')

        # 2. Get Session
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)

        # 3. Check Session Active
        if not session.is_active:
             return JsonResponse({'error': 'Class has ended!'}, status=400)

        # 4. Check Cooldown
        last_record = AttendanceRecord.objects.filter(student=request.user).order_by('-timestamp').first()
        if last_record:
            diff = timezone.now() - last_record.timestamp
            if diff < timedelta(minutes=60):
                return JsonResponse({'error': 'Attendance marked recently.'}, status=400)

        # 5. Check GPS
        if lat != 0:
            if not is_within_radius((lat, lng), (session.latitude, session.longitude), session.radius_meters):
                return JsonResponse({'error': 'You are too far from the class location.'}, status=400)

        if not captured_file:
            return JsonResponse({'error': 'No image received'}, status=400)

        # --- KEY CHANGE: SAVE TO DISK FIRST ---
        # We create the record immediately. This saves the image to media/ folder.
        record = AttendanceRecord.objects.create(
            session=session,
            student=request.user,
            captured_image=captured_file,
            gps_lat=lat,
            gps_long=lng,
            status='PENDING' # Status is pending until face check passes
        )

        # --- GET REFERENCE IMAGE PATH ---
        ref_path = None
        if hasattr(request.user, 'reference_image') and request.user.reference_image:
            ref_path = request.user.reference_image.path
        # elif request.user.profile_image:
        #     ref_path = request.user.profile_image.path
        
        if not ref_path:
            record.delete() # Cleanup
            return JsonResponse({'error': 'No profile photo found. Contact Admin.'}, status=400)

        # --- CHECK MATCH (Disk File vs Disk File) ---
        # Now we pass the paths, not the memory objects
        is_match = check_face_match(ref_path, record.captured_image.path)

        if is_match:
            # Update status to PRESENT
            record.status = 'PRESENT'
            record.save()
            
            return JsonResponse({
                'message': 'Success',
                'class_name': session.subject.name,
                'faculty_name': session.teacher.first_name,
                'topic': session.subject.code
            })
        else:
            # FAILED: Delete the temporary record so we don't store bad data
            record.delete()
            return JsonResponse({'error': 'Face mismatch. Please try again.'}, status=400)

    except Exception as e:
        print("SERVER ERROR:", e)
        return JsonResponse({'error': str(e)}, status=500)