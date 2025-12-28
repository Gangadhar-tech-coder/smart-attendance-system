# apps/attendance/views.py - IMPROVED verify_my_face function

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

# --- BASIC VIEWS (Keep as is) ---
def home(request): 
    return render(request, 'home.html')

@login_required
def select_class(request):
    subjects = Subject.objects.filter(staff=request.user)
    return render(request, 'select_class.html', {'subjects': subjects})

@login_required
def create_session(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
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


# --- IMPROVED FACE VERIFICATION ---
@csrf_exempt
def verify_my_face(request):
    """
    Enhanced face verification with detailed logging and better error handling
    """
    if request.method != 'POST': 
        return JsonResponse({'error': 'Invalid Method'}, status=405)
    
    if not request.user.is_authenticated: 
        return JsonResponse({'error': 'Session expired. Please login again.'}, status=401)

    print(f"\n{'='*60}")
    print(f"🎯 NEW ATTENDANCE REQUEST from {request.user.username}")
    print(f"{'='*60}")

    try:
        # ===== STEP 1: Parse Request Data =====
        session_id = request.POST.get('session')
        lat = float(request.POST.get('gps_lat', 0))
        lng = float(request.POST.get('gps_long', 0))
        captured_file = request.FILES.get('captured_image')

        print(f"\n📋 Request Data:")
        print(f"  - Session ID: {session_id}")
        print(f"  - GPS Coordinates: ({lat}, {lng})")
        print(f"  - Image Received: {captured_file is not None}")
        
        # ===== STEP 2: Validate Session =====
        try:
            session = AttendanceSession.objects.get(id=session_id)
            print(f"\n✅ Session Found:")
            print(f"  - Subject: {session.subject.name}")
            print(f"  - Teacher: {session.teacher.get_full_name()}")
            print(f"  - Active: {session.is_active}")
        except AttendanceSession.DoesNotExist:
            print("❌ Session not found in database")
            return JsonResponse({'error': 'Session not found'}, status=404)

        # ===== STEP 3: Check if Session is Active =====
        if not session.is_active:
            print("❌ Session has ended")
            return JsonResponse({'error': 'This class session has ended. Cannot mark attendance.'}, status=400)

        # ===== STEP 4: Check for Duplicate Attendance =====
        existing_record = AttendanceRecord.objects.filter(
            session=session,
            student=request.user
        ).first()
        
        if existing_record:
            print(f"⚠️ Duplicate attempt - Already marked as {existing_record.status}")
            return JsonResponse({
                'error': f'You have already marked attendance for this session (Status: {existing_record.status})',
                'already_marked': True
            }, status=400)

        # ===== STEP 5: Check Cooldown Period =====
        last_record = AttendanceRecord.objects.filter(
            student=request.user
        ).order_by('-timestamp').first()
        
        if last_record:
            time_diff = timezone.now() - last_record.timestamp
            cooldown_minutes = 5  # Adjust as needed
            
            if time_diff < timedelta(minutes=cooldown_minutes):
                remaining = cooldown_minutes - (time_diff.seconds // 60)
                print(f"⏳ Cooldown active - {remaining} minutes remaining")
                return JsonResponse({
                    'error': f'Please wait {remaining} more minutes before marking attendance again.'
                }, status=400)

        # ===== STEP 6: Verify GPS Location =====
        if lat != 0 and lng != 0:
            print(f"\n📍 Checking GPS location...")
            print(f"  - Student Location: ({lat}, {lng})")
            print(f"  - Class Location: ({session.latitude}, {session.longitude})")
            print(f"  - Allowed Radius: {session.radius_meters}m")
            
            if not is_within_radius((lat, lng), (session.latitude, session.longitude), session.radius_meters):
                print("❌ GPS verification failed - too far from class")
                return JsonResponse({
                    'error': 'You are too far from the class location. Please move closer to attend.'
                }, status=400)
            
            print("✅ GPS verification passed")
        else:
            print("⚠️ GPS coordinates not provided (lat/lng = 0)")

        # ===== STEP 7: Validate Image Upload =====
        if not captured_file:
            print("❌ No image file received")
            return JsonResponse({'error': 'Please capture your photo to mark attendance.'}, status=400)
        
        print(f"\n📸 Image Details:")
        print(f"  - Filename: {captured_file.name}")
        print(f"  - Size: {captured_file.size / 1024:.2f} KB")
        print(f"  - Content Type: {captured_file.content_type}")

        # ===== STEP 8: Create Temporary Attendance Record =====
        print(f"\n💾 Creating attendance record...")
        record = AttendanceRecord.objects.create(
            session=session,
            student=request.user,
            captured_image=captured_file,
            gps_lat=lat if lat != 0 else None,
            gps_long=lng if lng != 0 else None,
            status='PENDING'
        )
        print(f"✅ Record created with ID: {record.id}")
        print(f"  - Captured Image Path: {record.captured_image.path}")

        # ===== STEP 9: Get Reference Image =====
        ref_path = None
        
        # Try reference_image first
        if hasattr(request.user, 'reference_image') and request.user.reference_image:
            ref_path = request.user.reference_image.path
            print(f"\n📁 Using reference_image: {ref_path}")
        # Fallback to profile_image
        elif hasattr(request.user, 'profile_image') and request.user.profile_image:
            ref_path = request.user.profile_image.path
            print(f"\n📁 Using profile_image: {ref_path}")
        
        if not ref_path:
            print("❌ No reference image found for user")
            record.delete()
            return JsonResponse({
                'error': 'No profile photo found in your account. Please upload a profile picture in settings.'
            }, status=400)

        # ===== STEP 10: Perform Face Verification =====
        print(f"\n🤖 Starting AI Face Verification...")
        
        result = check_face_match(ref_path, record.captured_image.path, threshold=0.6)
        
        print(f"\n📊 Verification Result:")
        print(f"  - Match: {result['match']}")
        print(f"  - Confidence: {result['confidence']}%")
        print(f"  - Message: {result['message']}")

        # ===== STEP 11: Process Result =====
        if result['match']:
            # SUCCESS - Mark as Present
            record.status = 'present'
            record.save()
            
            print(f"\n✅ ATTENDANCE MARKED SUCCESSFULLY")
            print(f"  - Status: PRESENT")
            print(f"  - Confidence: {result['confidence']}%")
            
            return JsonResponse({
                'success': True,
                'message': 'Attendance marked successfully! ✓',
                'details': {
                    'class_name': session.subject.name,
                    'faculty_name': session.teacher.get_full_name(),
                    'topic': session.subject.code,
                    'confidence': result['confidence'],
                    'timestamp': record.timestamp.strftime('%I:%M %p')
                }
            })
        
        else:
            # FAILED - Delete record or keep as PENDING
            print(f"\n❌ FACE VERIFICATION FAILED")
            print(f"  - Confidence: {result['confidence']}%")
            print(f"  - Reason: {result['message']}")
            
            # Option 1: Delete the record (stricter)
            record.delete()
            
            # Option 2: Keep as PENDING for manual review (uncomment below)
            # record.status = 'PENDING'
            # record.save()
            
            return JsonResponse({
                'success': False,
                'error': result['message'],
                'details': {
                    'confidence': result['confidence'],
                    'suggestion': 'Please try again with better lighting or update your profile photo.'
                }
            }, status=400)

    except ValueError as e:
        print(f"\n❌ Value Error: {e}")
        return JsonResponse({
            'error': 'Invalid data format. Please try again.'
        }, status=400)
    
    except Exception as e:
        print(f"\n❌ CRITICAL SERVER ERROR:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Server error occurred. Please try again or contact support.',
            'technical_details': str(e)
        }, status=500)
    
    finally:
        print(f"\n{'='*60}")
        print(f"END OF REQUEST")
        print(f"{'='*60}\n")

# apps/attendance/views.py

# ... existing imports ...

@login_required
def view_reports(request):
    """List all sessions conducted by this teacher"""
    # Filter sessions where the teacher is the current user, ordered by newest first
    sessions = AttendanceSession.objects.filter(teacher=request.user).order_by('-start_time')
    return render(request, 'view_reports.html', {'sessions': sessions})

@login_required
def session_details(request, session_id):
    """Show attendance list for a specific past session"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Security: Ensure this teacher actually owns this session
    if session.teacher != request.user:
        return redirect('view_reports')

    records = AttendanceRecord.objects.filter(session=session).order_by('student__username')
    
    return render(request, 'session_details.html', {
        'session': session, 
        'records': records,
        'total_present': records.count()
    })


