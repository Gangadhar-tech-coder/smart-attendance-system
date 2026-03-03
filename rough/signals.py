# attendance/signals.py
"""
Signals for attendance automation and validation
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import AttendanceSession, AttendanceRecord


@receiver(pre_save, sender=AttendanceSession)
def validate_single_active_session(sender, instance, **kwargs):
    """
    Ensure a teacher can only have one active session at a time
    """
    if instance.is_active:
        existing = AttendanceSession.objects.filter(
            teacher=instance.teacher,
            is_active=True
        ).exclude(pk=instance.pk)
        
        if existing.exists():
            # Auto-end previous session
            for session in existing:
                session.end_session()
            print(f"⚠️ Auto-ended previous session for {instance.teacher.username}")


@receiver(post_save, sender=AttendanceSession)
def auto_create_attendance_records(sender, instance, created, **kwargs):
    """
    Optionally auto-create attendance records for all enrolled students
    when a session is created (marked as ABSENT by default)
    """
    if created and instance.is_active:
        from profiles.models import StudentProfile
        from academics.models import CourseEnrollment
        
        # Get all students enrolled in this course/subject
        students = []
        
        if instance.course:
            # Get students enrolled in this course
            enrollments = CourseEnrollment.objects.filter(
                course=instance.course,
                is_active=True
            ).select_related('student__user')
            students = [enrollment.student.user for enrollment in enrollments]
        
        elif instance.allocation:
            # Get students from semester and course
            if instance.allocation.course:
                enrollments = CourseEnrollment.objects.filter(
                    course=instance.allocation.course,
                    is_active=True
                ).select_related('student__user')
                students = [enrollment.student.user for enrollment in enrollments]
        
        # Create attendance records with ABSENT status by default
        for student in students:
            AttendanceRecord.objects.get_or_create(
                session=instance,
                student=student,
                defaults={'status': 'absent'}
            )
        
        if students:
            print(f"✓ Created {len(students)} attendance records for session {instance.session_code}")


@receiver(post_save, sender=AttendanceRecord)
def auto_verify_attendance(sender, instance, created, **kwargs):
    """
    Auto-verify attendance based on verification score and location
    """
    if created and instance.status == 'PENDING':
        # Auto-verify if verification score and location are good
        issues = instance.auto_verify()
        
        if not issues:
            print(f"✓ Auto-verified attendance for {instance.student.username}")
        else:
            print(f"⚠️ Attendance verification issues for {instance.student.username}: {issues}")


@receiver(post_save, sender=AttendanceRecord)
def update_status_based_on_time(sender, instance, **kwargs):
    """
    Update attendance status based on marking time
    """
    if instance.status == 'PENDING':
        from django.utils import timezone
        from datetime import timedelta
        
        time_diff = (timezone.now() - instance.session.start_time).total_seconds() / 60
        
        if time_diff <= 10:
            instance.status = 'present'
        elif time_diff <= 15:
            instance.status = 'late'
        else:
            instance.status = 'absent'
        
        instance.save()