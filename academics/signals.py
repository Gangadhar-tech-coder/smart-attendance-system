# academics/signals.py
"""
Signals for maintaining academic data consistency
"""

from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import (
    AcademicYear, Department, Course, SubjectAllocation, 
    CourseEnrollment, Semester
)


@receiver(pre_save, sender=AcademicYear)
def ensure_single_current_year(sender, instance, **kwargs):
    """
    Ensure only one academic year is marked as current
    """
    if instance.is_current:
        # Set all other years to not current
        AcademicYear.objects.exclude(pk=instance.pk).update(is_current=False)


@receiver(pre_save, sender=AcademicYear)
def sync_is_active_and_is_current(sender, instance, **kwargs):
    """
    Sync is_active with is_current
    If is_current=True, is_active should also be True
    """
    if instance.is_current and not instance.is_active:
        instance.is_active = True


@receiver(post_save, sender=Department)
def update_hod_user_type(sender, instance, **kwargs):
    """
    When a HOD is assigned to a department, ensure their user_type is 'hod'
    """
    if instance.hod:
        if instance.hod.user_type != 'hod':
            instance.hod.user_type = 'hod'
            instance.hod.save()


@receiver(post_save, sender=Course)
def auto_create_subject_if_missing(sender, instance, created, **kwargs):
    """
    If a course is created without a subject, optionally create one
    """
    if created and not instance.subject:
        from .models import Subject
        # Create a subject for this course
        subject, created = Subject.objects.get_or_create(
            subject_code=instance.code,
            defaults={
                'name': instance.name,
                'department': instance.department,
                'credits': instance.credits,
                'description': instance.description
            }
        )
        instance.subject = subject
        instance.save()


@receiver(post_save, sender=CourseEnrollment)
def sync_student_semester_on_enrollment(sender, instance, created, **kwargs):
    """
    When a student enrolls in a course, update their current_semester if needed
    """
    if created:
        from .models import Semester
        
        # Find appropriate semester based on course year
        course_year = instance.course.year
        semester_number = (course_year * 2) - 1  # Year 1 → Sem 1, Year 2 → Sem 3, etc.
        
        semester = Semester.objects.filter(
            academic_year=instance.course.academic_year,
            number=semester_number
        ).first()
        
        if semester and instance.student.current_semester != semester:
            instance.student.current_semester = semester
            instance.student.save()


@receiver(post_save, sender=SubjectAllocation)
def validate_allocation_consistency(sender, instance, created, **kwargs):
    """
    Ensure subject allocation is consistent
    """
    if instance.course:
        # If allocated to a course, ensure faculty's department matches
        if instance.faculty.department != instance.course.department:
            print(f"⚠️ Warning: Faculty {instance.faculty} is from {instance.faculty.department} "
                  f"but allocated to course in {instance.course.department}")