# profiles/models.py
"""
Enhanced Faculty and Student Profile models with PostgreSQL schema features
"""

from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from academics.models import Department, AcademicYear, Semester


class FacultyProfile(models.Model):
    """
    Enhanced Faculty Profile with additional fields from PostgreSQL schema
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='faculty_profile'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,  # Changed from SET_NULL to PROTECT
        related_name='faculty_members',
        null=True
    )
    
    # Employee ID with validation
    staff_id = models.CharField(
        max_length=20, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^FAC-\d{4}$',
                message='Employee ID must be in format FAC-XXXX (e.g., FAC-0001).',
                code='invalid_staff_id'
            )
        ]
    )
    
    # NEW: Additional fields from PostgreSQL schema
    designation = models.CharField(
        max_length=100,
        help_text="e.g., Professor, Associate Professor, Assistant Professor",
        null=True,
        blank=True
    )
    joining_date = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faculty'
        verbose_name_plural = 'Faculty'
        indexes = [
            models.Index(fields=['staff_id']),
            models.Index(fields=['department']),
        ]
 
    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()}"
    
    def get_teaching_load(self):
        """Get all active course allocations"""
        return self.allocations.filter(is_active=True)


class StudentProfile(models.Model):
    """
    Enhanced Student Profile with additional fields from PostgreSQL schema
    """
    YEAR_CHOICES = [(i, f'Year {i}') for i in range(1, 5)]
    SECTION_CHOICES = [
        ('A', 'Section A'),
        ('B', 'Section B'),
        ('C', 'Section C'),
        ('D', 'Section D'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        related_name='students',
        null=True
    )
    academic_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.PROTECT,
        related_name='students',
        null=True
    )
    current_semester = models.ForeignKey(
        Semester, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='students'
    )
    roll_number = models.CharField(max_length=20, unique=True)
    
    # NEW: Additional fields from PostgreSQL schema
    year = models.IntegerField(
        choices=YEAR_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Current year of study",
        null=True
    )
    section = models.CharField(
        max_length=1, 
        choices=SECTION_CHOICES,
        help_text="Class section",
        null=True
    )
    admission_date = models.DateField(null=True, blank=True)
    
    # Face recognition data (already in User model, but can be duplicated here)
    face_encoding = models.TextField(blank=True, null=True)
    
    # Contact information
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        indexes = [
            models.Index(fields=['roll_number']),
            models.Index(fields=['department', 'year', 'section']),
            models.Index(fields=['academic_year']),
        ]

    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name()}"
    
    def get_enrolled_courses(self):
        """Get all active course enrollments"""
        return self.course_enrollments.filter(is_active=True)
    
    def calculate_attendance_percentage(self, course=None):
        """Calculate attendance percentage"""
        from attendance.models import AttendanceRecord
        
        records = AttendanceRecord.objects.filter(student=self.user)
        
        if course:
            records = records.filter(session__subject=course)
        
        total = records.count()
        if total == 0:
            return 0.0
        
        present = records.filter(status='present').count()
        return (present / total) * 100


class HODProfile(models.Model):
    """
    NEW: Separate HOD Profile for department heads
    Optional - you can also just use FacultyProfile with user_type='hod'
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hod_profile',
        limit_choices_to={'user_type': 'hod'}
    )
    
    # HOD manages a department (but Department already has hod field)
    # This creates a bidirectional relationship
    
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