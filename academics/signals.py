# academics/signals.py
"""
Signals for FINAL academic structure
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import (
    AcademicYear, Department, Course, Semester, 
    Subject, SubjectAllocation, CourseAllocation, Section
)


@receiver(pre_save, sender=AcademicYear)
def ensure_single_current_year(sender, instance, **kwargs):
    """Ensure only one academic year is marked as current"""
    if instance.is_current:
        AcademicYear.objects.exclude(pk=instance.pk).update(is_current=False)
    if instance.is_active:
        AcademicYear.objects.exclude(pk=instance.pk).update(is_active=False)


@receiver(post_save, sender=Department)
def update_hod_user_type(sender, instance, **kwargs):
    """When a HOD is assigned to a department, ensure their user_type is 'hod'"""
    if instance.hod:
        if instance.hod.user_type != 'hod':
            instance.hod.user_type = 'hod'
            instance.hod.save()
            print(f"✓ Updated {instance.hod.username} to HOD user type")


@receiver(post_save, sender=AcademicYear)
def auto_create_semesters_for_all_courses(sender, instance, created, **kwargs):
    """
    When a new academic year is created, create semesters for all active courses
    """
    if created:
        from datetime import timedelta
        
        courses = Course.objects.filter(is_active=True)
        
        for course in courses:
            year_duration = (instance.end_date - instance.start_date).days
            semester_duration = year_duration // course.total_semesters
            
            for sem_num in range(1, course.total_semesters + 1):
                start_date = instance.start_date + timedelta(days=(sem_num - 1) * semester_duration)
                end_date = instance.start_date + timedelta(days=sem_num * semester_duration - 1)
                
                if sem_num == course.total_semesters:
                    end_date = instance.end_date
                
                semester, sem_created = Semester.objects.get_or_create(
                    academic_year=instance,
                    course=course,
                    semester_number=sem_num,
                    defaults={
                        'start_date': start_date,
                        'end_date': end_date,
                        'is_active': sem_num in [1, 2]
                    }
                )
                
                if sem_created:
                    print(f"✓ Created {semester}")


@receiver(post_save, sender=Course)
def auto_create_semesters_for_new_course(sender, instance, created, **kwargs):
    """
    When a new course is created, create semesters for current academic year
    """
    if created:
        from datetime import timedelta
        
        # Get current academic year
        current_ay = AcademicYear.objects.filter(is_current=True).first()
        
        if current_ay:
            year_duration = (current_ay.end_date - current_ay.start_date).days
            semester_duration = year_duration // instance.total_semesters
            
            for sem_num in range(1, instance.total_semesters + 1):
                start_date = current_ay.start_date + timedelta(days=(sem_num - 1) * semester_duration)
                end_date = current_ay.start_date + timedelta(days=sem_num * semester_duration - 1)
                
                if sem_num == instance.total_semesters:
                    end_date = current_ay.end_date
                
                semester, sem_created = Semester.objects.get_or_create(
                    academic_year=current_ay,
                    course=instance,
                    semester_number=sem_num,
                    defaults={
                        'start_date': start_date,
                        'end_date': end_date,
                        'is_active': sem_num in [1, 2]
                    }
                )
                
                if sem_created:
                    print(f"✓ Created {semester}")


@receiver(post_save, sender=Subject)
def auto_create_course_for_subject(sender, instance, created, **kwargs):
    """
    OPTIONAL: Auto-create a course entry when subject is created
    This is what was causing your confusion - disable if not needed
    """
    # DISABLED - Uncomment only if you want this behavior
    # if created:
    #     from .models import AcademicYear, Section, CourseDepartment
    #     
    #     current_ay = AcademicYear.objects.filter(is_current=True).first()
    #     if not current_ay:
    #         return
    #     
    #     # Get or create course department
    #     cd, _ = CourseDepartment.objects.get_or_create(
    #         course=instance.course,
    #         department=instance.department
    #     )
    #     
    #     # Create section for year 1, section A
    #     section, created = Section.objects.get_or_create(
    #         course_department=cd,
    #         academic_year=current_ay,
    #         year=1,
    #         section_letter='A',
    #         defaults={
    #             'current_semester': instance.semester,
    #             'is_active': True
    #         }
    #     )
    #     
    #     if created:
    #         print(f"✓ Auto-created Section: {section.full_name}")
    pass


@receiver(post_save, sender=CourseAllocation)
def sync_student_info_on_allocation(sender, instance, created, **kwargs):
    """
    When a student is allocated to a course, update their information
    """
    if created:
        print(f"✓ Allocated {instance.roll_number} to {instance.section.full_name}")


@receiver(post_save, sender=SubjectAllocation)
def validate_allocation_consistency(sender, instance, created, **kwargs):
    """
    Ensure subject allocation is consistent
    """
    if created:
        # Check if faculty's department matches subject's department
        if instance.faculty.department != instance.subject.department:
            print(f"⚠️ Warning: Faculty {instance.faculty.user.username} is from {instance.faculty.department} "
                  f"but allocated to subject in {instance.subject.department}")
        
        print(f"✓ Allocated {instance.subject.name} to {instance.faculty.user.get_full_name()} for {instance.section.full_name}")


@receiver(pre_save, sender=SubjectAllocation)
def validate_subject_section_match(sender, instance, **kwargs):
    """
    Validate that subject matches section before saving
    """
    if instance.subject.course != instance.section.course_department.course:
        raise ValidationError(
            f"Subject is for {instance.subject.course.short_name} but section is for {instance.section.course_department.course.short_name}"
        )
    if instance.subject.department != instance.section.course_department.department:
        raise ValidationError(
            f"Subject is for {instance.subject.department.code} but section is for {instance.section.course_department.department.code}"
        )