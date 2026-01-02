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


# apps/attendance/views.py - Add these new views

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q
from apps.accounts.models import User, Subject
from apps.attendance.models import AttendanceSession, AttendanceRecord
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime

@login_required
def attendance_calculator(request):
    """
    Attendance calculation dashboard for faculty
    Shows attendance statistics for all students in their subjects
    """
    if request.user.user_type != 'staff':
        return redirect('dashboard')
    
    # Get selected subject from query parameter
    selected_subject_id = request.GET.get('subject')
    
    # Get all subjects taught by this faculty
    subjects = Subject.objects.filter(staff=request.user)
    
    # Default to first subject if none selected
    if not selected_subject_id and subjects.exists():
        selected_subject = subjects.first()
    elif selected_subject_id:
        selected_subject = get_object_or_404(Subject, id=selected_subject_id, staff=request.user)
    else:
        # No subjects assigned
        return render(request, 'attendance_calculator.html', {
            'subjects': subjects,
            'selected_subject': None,
            'attendance_data': [],
            'stats': {}
        })
    
    # Get all sessions for this subject by this faculty
    all_sessions = AttendanceSession.objects.filter(
        teacher=request.user,
        subject=selected_subject
    ).order_by('start_time')
    
    total_sessions = all_sessions.count()
    
    # Get all students who have attended at least once (or get from enrollment if you have it)
    # For now, we'll get unique students from attendance records
    # Note: Use 'attendancerecord' (lowercase) - the related_name from AttendanceRecord model
    students_with_records = User.objects.filter(
        user_type='student',
        attendancerecord__session__in=all_sessions
    ).distinct().order_by('student_id')
    
    # Calculate attendance for each student
    attendance_data = []
    
    for student in students_with_records:
        # Count present days
        present_count = AttendanceRecord.objects.filter(
            student=student,
            session__in=all_sessions,
            status='present'
        ).count()
        
        # Count total marked (present + absent + pending)
        total_marked = AttendanceRecord.objects.filter(
            student=student,
            session__in=all_sessions
        ).count()
        
        # Calculate percentage based on total sessions
        if total_sessions > 0:
            percentage = (present_count / total_sessions) * 100
        else:
            percentage = 0
        
        attendance_data.append({
            'student': student,
            'roll_number': student.student_id or 'N/A',
            'name': student.get_full_name() or student.username,
            'total_days': total_sessions,
            'present_days': present_count,
            'absent_days': total_sessions - present_count,
            'percentage': round(percentage, 2)
        })
    
    # Sort by roll number
    attendance_data.sort(key=lambda x: x['roll_number'])
    
    # Calculate overall statistics
    if attendance_data:
        total_students = len(attendance_data)
        avg_attendance = sum(d['percentage'] for d in attendance_data) / total_students
        students_above_75 = sum(1 for d in attendance_data if d['percentage'] >= 75)
        students_below_75 = total_students - students_above_75
    else:
        total_students = 0
        avg_attendance = 0
        students_above_75 = 0
        students_below_75 = 0
    
    stats = {
        'total_students': total_students,
        'total_sessions': total_sessions,
        'avg_attendance': round(avg_attendance, 2),
        'students_above_75': students_above_75,
        'students_below_75': students_below_75
    }
    
    return render(request, 'attendance_calculator.html', {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'attendance_data': attendance_data,
        'stats': stats
    })


@login_required
def download_attendance_excel(request):
    """
    Download attendance data as Excel file
    """
    if request.user.user_type != 'staff':
        return redirect('dashboard')
    
    subject_id = request.GET.get('subject')
    
    if not subject_id:
        return HttpResponse("Subject ID required", status=400)
    
    selected_subject = get_object_or_404(Subject, id=subject_id, staff=request.user)
    
    # Get all sessions for this subject
    all_sessions = AttendanceSession.objects.filter(
        teacher=request.user,
        subject=selected_subject
    ).order_by('start_time')
    
    total_sessions = all_sessions.count()
    
    # Get students
    # Note: Use 'attendancerecord' (lowercase, no underscore)
    students_with_records = User.objects.filter(
        user_type='student',
        attendancerecord__session__in=all_sessions
    ).distinct().order_by('student_id')
    
    # Calculate attendance data
    attendance_data = []
    for student in students_with_records:
        present_count = AttendanceRecord.objects.filter(
            student=student,
            session__in=all_sessions,
            status='present'
        ).count()
        
        if total_sessions > 0:
            percentage = (present_count / total_sessions) * 100
        else:
            percentage = 0
        
        attendance_data.append({
            'roll_number': student.student_id or 'N/A',
            'name': student.get_full_name() or student.username,
            'email': student.email,
            'total_days': total_sessions,
            'present_days': present_count,
            'absent_days': total_sessions - present_count,
            'percentage': round(percentage, 2)
        })
    
    attendance_data.sort(key=lambda x: x['roll_number'])
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    
    # Define styles
    header_fill = PatternFill(start_color="1E3C72", end_color="1E3C72", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Title
    ws.merge_cells('A1:G1')
    title_cell = ws['A1']
    title_cell.value = f"Attendance Report - {selected_subject.name}"
    title_cell.font = Font(bold=True, size=16)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Metadata
    ws['A2'] = f"Subject Code: {selected_subject.code}"
    ws['A3'] = f"Faculty: {request.user.get_full_name() or request.user.username}"
    ws['A4'] = f"Total Sessions: {total_sessions}"
    ws['A5'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Headers
    headers = ['S.No', 'Roll Number', 'Student Name', 'Email', 'Total Days', 'Present Days', 'Absent Days', 'Percentage (%)']
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    
    # Data rows
    for idx, data in enumerate(attendance_data, 1):
        row_num = 7 + idx
        
        # S.No
        ws.cell(row=row_num, column=1, value=idx).border = border
        
        # Roll Number
        ws.cell(row=row_num, column=2, value=data['roll_number']).border = border
        
        # Name
        ws.cell(row=row_num, column=3, value=data['name']).border = border
        
        # Email
        ws.cell(row=row_num, column=4, value=data['email']).border = border
        
        # Total Days
        ws.cell(row=row_num, column=5, value=data['total_days']).border = border
        
        # Present Days
        cell_present = ws.cell(row=row_num, column=6, value=data['present_days'])
        cell_present.border = border
        
        # Absent Days
        cell_absent = ws.cell(row=row_num, column=7, value=data['absent_days'])
        cell_absent.border = border
        
        # Percentage
        cell_percentage = ws.cell(row=row_num, column=8, value=data['percentage'])
        cell_percentage.border = border
        cell_percentage.alignment = Alignment(horizontal='center')
        
        # Color code percentage
        if data['percentage'] >= 75:
            cell_percentage.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            cell_percentage.font = Font(color="006100", bold=True)
        elif data['percentage'] >= 50:
            cell_percentage.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            cell_percentage.font = Font(color="9C6500")
        else:
            cell_percentage.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            cell_percentage.font = Font(color="9C0006", bold=True)
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 14
    ws.column_dimensions['G'].width = 14
    ws.column_dimensions['H'].width = 15
    
    # Summary statistics
    summary_row = 7 + len(attendance_data) + 2
    ws.cell(row=summary_row, column=1, value="Summary Statistics").font = Font(bold=True, size=12)
    
    ws.cell(row=summary_row + 1, column=1, value="Total Students:")
    ws.cell(row=summary_row + 1, column=2, value=len(attendance_data))
    
    ws.cell(row=summary_row + 2, column=1, value="Students Above 75%:")
    above_75 = sum(1 for d in attendance_data if d['percentage'] >= 75)
    ws.cell(row=summary_row + 2, column=2, value=above_75)
    
    ws.cell(row=summary_row + 3, column=1, value="Students Below 75%:")
    ws.cell(row=summary_row + 3, column=2, value=len(attendance_data) - above_75)
    
    if attendance_data:
        avg_percentage = sum(d['percentage'] for d in attendance_data) / len(attendance_data)
        ws.cell(row=summary_row + 4, column=1, value="Average Attendance:")
        ws.cell(row=summary_row + 4, column=2, value=f"{avg_percentage:.2f}%")
    
    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename = f"Attendance_{selected_subject.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response