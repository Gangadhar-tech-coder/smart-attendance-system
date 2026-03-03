# profiles/models.py
"""
FINAL Profiles for Course-based structure
"""

from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class FacultyProfile(models.Model):
    """Faculty Profile"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='faculty_profile'
    )
    department = models.ForeignKey(
        'academics.Department', 
        on_delete=models.PROTECT,
        related_name='faculty_members',
        null=True,
        blank=True
    )
    
    staff_id = models.CharField(max_length=20, unique=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faculty'
        verbose_name_plural = 'Faculty'
 
    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()}"
    
    def get_teaching_assignments(self):
        """Get all active subject allocations (teaching assignments)"""
        return self.subject_allocations.filter(is_active=True).select_related(
            'subject', 'section__course_department__course', 
            'section__course_department__department'
        )


class StudentProfile(models.Model):
    """
    Student Profile
    Course allocation is done separately via CourseAllocation model
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    roll_number = models.CharField(
        max_length=30,
        unique=True,
        help_text="Student roll number",
        null=True
    )
    
    # Basic info
    admission_date = models.DateField(null=True, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Face recognition
    face_encoding = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'

    def __str__(self):
        if hasattr(self, 'course_allocation'):
            return f"{self.course_allocation.roll_number} - {self.user.get_full_name()}"
        return f"{self.user.get_full_name()}"
    
    def get_course_info(self):
        """
        Get student's course information
        Returns dict with: course, department, year, section, semester
        """
        try:
            allocation = self.course_allocation
            return {
                'course': allocation.course.short_name,
                'department': allocation.department.code,
                'year': allocation.year,
                'section': allocation.section.section_letter,
                'semester': allocation.current_semester.semester_number if allocation.current_semester else None,
                'full_section': allocation.section.full_name,
                'roll_number': allocation.roll_number
            }
        except:
            return None
    
    def get_current_subjects(self):
        """Get subjects for current semester"""
        try:
            allocation = self.course_allocation
            if allocation.current_semester:
                from academics.models import Subject
                return Subject.objects.filter(
                    course=allocation.course,
                    department=allocation.department,
                    semester=allocation.current_semester,
                    is_active=True
                )
        except:
            return []
        return []
    
    def get_allocated_subjects_with_faculty(self):
        """Get subjects with their allocated faculty for this student's section"""
        try:
            allocation = self.course_allocation
            from academics.models import SubjectAllocation
            
            return SubjectAllocation.objects.filter(
                section=allocation.section,
                is_active=True
            ).select_related('subject', 'faculty__user')
        except:
            return []


class HODProfile(models.Model):
    """HOD Profile"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hod_profile',
        limit_choices_to={'user_type': 'hod'}
    )
    
    appointment_date = models.DateField(null=True, blank=True)
    responsibilities = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'hod_profiles'
        verbose_name = 'HOD Profile'
        verbose_name_plural = 'HOD Profiles'
    
    def __str__(self):
        return f"HOD - {self.user.get_full_name()}"
    
    def get_department(self):
        """Get the department this HOD heads"""
        try:
            return self.user.headed_department
        except:
            return None