# apps/attendance/views.py - CORRECTED VERSION

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import AttendanceSession, AttendanceRecord
from apps.accounts.models import Subject
from .utils import is_within_radius, check_face_match

# --- BASIC VIEWS ---
def home(request): 
    return render(request, 'home.html')

@login_required
def select_class(request):
    subjects = Subject.objects.filter(staff=request.user)
    return render(request, 'select_class.html', {'subjects': subjects})

@login_required
def create_session(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if faculty already has an active session
    existing_active = AttendanceSession.objects.filter(
        teacher=request.user,
        is_active=True
    ).first()
    
    if existing_active:
        # Redirect to monitor existing session
        return redirect('monitor_session', session_id=existing_active.id)
    
    # Create new session
    session = AttendanceSession.objects.create(
        teacher=request.user, 
        subject=subject, 
        is_active=True,
        latitude=17.4468,  # Update to your college coordinates
        longitude=78.4468,
        radius_meters=20000  # 20km radius
    )
    return redirect('monitor_session', session_id=session.id)

@login_required
def monitor_session(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Security: Ensure this session belongs to this faculty
    if session.teacher != request.user:
        return redirect('dashboard')
    
    # Get attendance records for this session
    records = AttendanceRecord.objects.filter(
        session=session
    ).select_related('student').order_by('-timestamp')
    
    # Calculate statistics
    total_present = records.filter(status='present').count()
    total_pending = records.filter(status='PENDING').count()
    
    return render(request, 'monitor_session.html', {
        'session': session,
        'records': records,
        'total_present': total_present,
        'total_pending': total_pending,
    })

@login_required
def end_session(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Security check
    if session.teacher != request.user:
        return redirect('dashboard')
    
    session.is_active = False
    session.end_time = timezone.now()
    session.save()
    
    return redirect('dashboard')

@login_required
def view_reports(request):
    """List all sessions conducted by this teacher"""
    sessions = AttendanceSession.objects.filter(
        teacher=request.user
    ).select_related('subject').order_by('-start_time')
    
    return render(request, 'view_reports.html', {'sessions': sessions})

@login_required
def session_details(request, session_id):
    """Show attendance list for a specific session"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    
    # Security: Ensure this teacher owns this session
    if session.teacher != request.user:
        return redirect('view_reports')
    
    records = AttendanceRecord.objects.filter(
        session=session
    ).select_related('student').order_by('student__username')
    
    total_present = records.filter(status='present').count()
    total_pending = records.filter(status='PENDING').count()
    
    return render(request, 'session_details.html', {
        'session': session, 
        'records': records,
        'total_present': total_present,
        'total_pending': total_pending,
    })


# --- FACE VERIFICATION API ---
@csrf_exempt
def verify_my_face(request):
    """
    API endpoint for student attendance marking with face verification
    """
    if request.method != 'POST': 
        return JsonResponse({'error': 'Invalid Method'}, status=405)
    
    if not request.user.is_authenticated: 
        return JsonResponse({'error': 'Session expired. Please login again.'}, status=401)

    print(f"\n{'='*60}")
    print(f"🎯 ATTENDANCE REQUEST from {request.user.username}")
    print(f"{'='*60}")

    try:
        # ===== PARSE REQUEST =====
        session_id = request.POST.get('session')
        lat = float(request.POST.get('gps_lat', 0))
        lng = float(request.POST.get('gps_long', 0))
        captured_file = request.FILES.get('captured_image')

        print(f"\n📋 Request Data:")
        print(f"  - Session ID: {session_id}")
        print(f"  - GPS: ({lat}, {lng})")
        print(f"  - Image: {captured_file is not None}")
        
        # ===== VALIDATE SESSION =====
        try:
            session = AttendanceSession.objects.get(id=session_id)
            print(f"\n✅ Session: {session.subject.name}")
        except AttendanceSession.DoesNotExist:
            print("❌ Session not found")
            return JsonResponse({'error': 'Session not found'}, status=404)

        # ===== CHECK SESSION ACTIVE =====
        if not session.is_active:
            print("❌ Session ended")
            return JsonResponse({
                'error': 'This class session has ended.'
            }, status=400)

        # ===== CHECK DUPLICATE =====
        existing = AttendanceRecord.objects.filter(
            session=session,
            student=request.user
        ).first()
        
        if existing:
            print(f"⚠️ Already marked: {existing.status}")
            return JsonResponse({
                'error': f'Attendance already marked ({existing.status})',
                'already_marked': True
            }, status=400)

        # ===== VALIDATE IMAGE =====
        if not captured_file:
            print("❌ No image")
            return JsonResponse({
                'error': 'Please capture your photo.'
            }, status=400)
        
        print(f"\n📸 Image: {captured_file.name} ({captured_file.size / 1024:.2f} KB)")

        # ===== VERIFY GPS (Optional) =====
        if lat != 0 and lng != 0:
            print(f"\n📍 GPS Check:")
            print(f"  - Student: ({lat}, {lng})")
            print(f"  - Class: ({session.latitude}, {session.longitude})")
            print(f"  - Radius: {session.radius_meters}m")
            
            if not is_within_radius(
                (lat, lng), 
                (session.latitude, session.longitude), 
                session.radius_meters
            ):
                print("❌ Too far from class")
                return JsonResponse({
                    'error': 'You are too far from the class location.'
                }, status=400)
            
            print("✅ GPS OK")

        # ===== CREATE RECORD =====
        print(f"\n💾 Creating record...")
        record = AttendanceRecord.objects.create(
            session=session,
            student=request.user,
            captured_image=captured_file,
            gps_lat=lat if lat != 0 else None,
            gps_long=lng if lng != 0 else None,
            status='PENDING'
        )
        print(f"✅ Record ID: {record.id}")

        # ===== GET REFERENCE IMAGE =====
        ref_path = None
        
        if hasattr(request.user, 'reference_image') and request.user.reference_image:
            ref_path = request.user.reference_image.path
            print(f"\n📁 Reference: reference_image")
        elif hasattr(request.user, 'profile_image') and request.user.profile_image:
            ref_path = request.user.profile_image.path
            print(f"\n📁 Reference: profile_image")
        
        if not ref_path:
            print("❌ No reference image")
            record.delete()
            return JsonResponse({
                'error': 'No profile photo found. Please upload one in settings.'
            }, status=400)

        # ===== FACE VERIFICATION =====
        print(f"\n🤖 Face Verification...")
        
        result = check_face_match(
            ref_path, 
            record.captured_image.path, 
            threshold=0.5
        )
        
        print(f"\n📊 Result:")
        print(f"  - Match: {result['match']}")
        print(f"  - Confidence: {result['confidence']}%")

        # ===== PROCESS RESULT =====
        if result['match']:
            # SUCCESS
            record.status = 'present'
            record.save()
            
            print(f"\n✅ ATTENDANCE MARKED")
            
            return JsonResponse({
                'success': True,
                'message': 'Attendance marked successfully!',
                'details': {
                    'class_name': session.subject.name,
                    'faculty_name': session.teacher.get_full_name() or session.teacher.username,
                    'topic': session.subject.code,
                    'confidence': result['confidence'],
                    'timestamp': record.timestamp.strftime('%I:%M %p')
                }
            })
        
        else:
            # FAILED
            print(f"\n❌ VERIFICATION FAILED")
            record.delete()
            
            return JsonResponse({
                'success': False,
                'error': result['message'],
                'details': {
                    'confidence': result['confidence'],
                    'suggestion': 'Try again with better lighting.'
                }
            }, status=400)

    except ValueError as e:
        print(f"\n❌ ValueError: {e}")
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': 'Server error. Please try again.',
            'technical_details': str(e)
        }, status=500)
    
    finally:
        print(f"\n{'='*60}\n")