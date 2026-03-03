# accounts/signals.py
"""
Signals for automatic profile creation with FINAL structure
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile when a User is created
    """
    if created:
        from profiles.models import FacultyProfile, StudentProfile, HODProfile
        from academics.models import Department
        
        if instance.user_type == 'staff':
            # Create Faculty Profile
            department = None
            if instance.department:
                department = Department.objects.filter(code=instance.department).first()
            
            # Generate staff_id
            last_faculty = FacultyProfile.objects.order_by('-id').first()
            if last_faculty and last_faculty.staff_id:
                try:
                    last_id = int(last_faculty.staff_id.split('-')[1])
                    staff_id = f'FAC-{last_id + 1:04d}'
                except:
                    staff_id = f'FAC-{FacultyProfile.objects.count() + 1:04d}'
            else:
                staff_id = f'FAC-0001'
            
            FacultyProfile.objects.create(
                user=instance,
                staff_id=staff_id,
                department=department,
                designation='Faculty Member'
            )
            print(f"✓ Created Faculty Profile: {staff_id} for {instance.username}")
        
        elif instance.user_type == 'student':
            # Create Student Profile (without course allocation yet)
            # Course allocation must be done separately via CourseAllocation model
            
            StudentProfile.objects.create(
                user=instance,
            )
            print(f"✓ Created Student Profile for {instance.username}")
            print(f"  ⚠️ Remember to create CourseAllocation to assign section and roll number")
        
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
        from profiles.models import FacultyProfile
        
        try:
            if instance.user_type == 'staff' and hasattr(instance, 'faculty_profile'):
                from academics.models import Department
                if instance.department:
                    department = Department.objects.filter(code=instance.department).first()
                    if department and instance.faculty_profile.department != department:
                        instance.faculty_profile.department = department
                        instance.faculty_profile.save()
                        print(f"✓ Updated {instance.username} department to {department.code}")
        
        except Exception as e:
            print(f"Error updating profile: {e}")