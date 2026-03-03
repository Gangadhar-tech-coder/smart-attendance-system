# attendance/signals.py
"""
FINAL Attendance Signals
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import AttendanceSession, AttendanceRecord


@receiver(pre_save, sender=AttendanceSession)
def validate_single_active_session(sender, instance, **kwargs):
    """Ensure a teacher can only have one active session at a time"""
    if instance.is_active:
        existing = AttendanceSession.objects.filter(
            teacher=instance.teacher,
            is_active=True
        ).exclude(pk=instance.pk)
        
        if existing.exists():
            for session in existing:
                session.end_session()
            print(f"⚠️ Auto-ended previous session for {instance.teacher.username}")


@receiver(post_save, sender=AttendanceSession)
def auto_create_attendance_records(sender, instance, created, **kwargs):
    """Auto-create attendance records for all students in section"""
    if created and instance.is_active:
        from academics.models import CourseAllocation
        
        # Get all students in this section
        student_allocations = CourseAllocation.objects.filter(
            section=instance.subject_allocation.section,
            is_active=True
        ).select_related('student__user')
        
        # Create attendance records
        created_count = 0
        for student_alloc in student_allocations:
            AttendanceRecord.objects.get_or_create(
                session=instance,
                student=student_alloc.student.user,
                defaults={'status': 'absent'}
            )
            created_count += 1
        
        if created_count > 0:
            print(f"✓ Created {created_count} attendance records for session {instance.session_code}")


@receiver(post_save, sender=AttendanceRecord)
def update_status_based_on_time(sender, instance, created, **kwargs):
    """Update attendance status based on marking time"""
    if instance.status == 'PENDING' and not created:
        from django.utils import timezone
        
        time_diff = (timezone.now() - instance.session.start_time).total_seconds() / 60
        
        if time_diff <= 10:
            instance.status = 'present'
            instance.save(update_fields=['status'])
        elif time_diff <= 15:
            instance.status = 'late'
            instance.save(update_fields=['status'])