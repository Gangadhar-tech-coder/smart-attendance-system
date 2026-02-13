# accounts/signals.py
"""
Signals for automatic profile creation when users are created
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile when a User is created
    based on their user_type
    """
    if created:
        # Import here to avoid circular imports
        from profiles.models import FacultyProfile, StudentProfile, HODProfile
        from academics.models import Department
        
        if instance.user_type == 'staff':
            # Create Faculty Profile
            # Get department if specified
            department = None
            if instance.department:
                department = Department.objects.filter(code=instance.department).first()
            
            # Generate staff_id
            last_faculty = FacultyProfile.objects.order_by('-id').first()
            try:
                if last_faculty and '-' in last_faculty.staff_id:
                    last_id = int(last_faculty.staff_id.split('-')[1])
                    new_id = f"FAC-{last_id + 1:03d}"
                else:
                    new_id = "FAC-001"
            except (ValueError, IndexError):
                new_id = "FAC-001"
            
            FacultyProfile.objects.create(
                user=instance,
                staff_id=new_id,
                department=department,
                designation='Faculty Member'  # Default designation
            )
            print(f"✓ Created Faculty Profile for {instance.username}")
        
        elif instance.user_type == 'student':
            # Create Student Profile
            from academics.models import AcademicYear
            
            # Get department
            department = None
            if instance.department:
                department = Department.objects.filter(code=instance.department).first()
            
            # Get current academic year
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            
            # Use student_id from User or generate roll_number
            roll_number = instance.student_id if instance.student_id else f'STU-{instance.id:06d}'
            
            StudentProfile.objects.create(
                user=instance,
                roll_number=roll_number,
                department=department,
                academic_year=academic_year,
                year=1,  # Default to first year
                section='A'  # Default section
            )
            print(f"✓ Created Student Profile for {instance.username}")
        
        elif instance.user_type == 'hod':
            # Create HOD Profile
            HODProfile.objects.create(
                user=instance
            )
            print(f"✓ Created HOD Profile for {instance.username}")


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    """
    Update profile when user is updated
    """
    if not created:
        # Import here to avoid circular imports
        from profiles.models import FacultyProfile, StudentProfile
        
        try:
            if instance.user_type == 'staff' and hasattr(instance, 'faculty_profile'):
                # Update faculty profile department if changed
                from academics.models import Department
                if instance.department:
                    department = Department.objects.filter(code=instance.department).first()
                    if department and instance.faculty_profile.department != department:
                        instance.faculty_profile.department = department
                        instance.faculty_profile.save()
            
            elif instance.user_type == 'student' and hasattr(instance, 'student_profile'):
                # Update student profile
                from academics.models import Department
                if instance.department:
                    department = Department.objects.filter(code=instance.department).first()
                    if department and instance.student_profile.department != department:
                        instance.student_profile.department = department
                        instance.student_profile.save()
                
                # Update roll number if student_id changed
                if instance.student_id and instance.student_profile.roll_number != instance.student_id:
                    instance.student_profile.roll_number = instance.student_id
                    instance.student_profile.save()
        except Exception as e:
            print(f"Error updating profile: {e}")