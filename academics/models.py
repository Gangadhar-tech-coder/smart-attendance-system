# academics/models.py
"""
Enhanced Academic models integrating PostgreSQL schema features
"""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings


class Department(models.Model):
    """
    Department model with HOD assignment capability
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=10, 
        unique=True, 
        help_text="e.g., CSE, ECE, MECH",
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{3,10}$',
                message='Department code must be 3-10 uppercase letters.'
            )
        ]
    )
    description = models.TextField(blank=True, null=True)
    
    # NEW: Link to HOD
    hod = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department',
        limit_choices_to={'user_type': 'hod'}
    )
    
    # NEW: Active status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    
    class Meta:
        db_table = 'departments'
        indexes = [
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicYear(models.Model):
    """
    Academic Year model with validation
    """
    name = models.CharField(
        max_length=20, 
        help_text="e.g., 2023-2024",
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{2,4}$',
                message='Year must be in format YYYY-YY or YYYY-YYYY'
            )
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(
        default=False, 
        help_text="Check this if this is the current academic year"
    )
    
    # NEW: Renamed from is_active to is_current for clarity
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    
    class Meta:
        db_table = 'academic_years'
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        """Validate that end_date is after start_date"""
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one academic year is active/current at a time
        if self.is_active or self.is_current:
            AcademicYear.objects.filter(is_active=True).update(is_active=False)
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    """
    Semester model linked to academic year
    """
    SEMESTER_CHOICES = [
        (1, 'Semester 1'), (2, 'Semester 2'), (3, 'Semester 3'),
        (4, 'Semester 4'), (5, 'Semester 5'), (6, 'Semester 6'),
        (7, 'Semester 7'), (8, 'Semester 8'),
    ]
    
    academic_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.CASCADE, 
        related_name='semesters'
    )
    number = models.IntegerField(choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # NEW: Active status
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('academic_year', 'number')
        db_table = 'semesters'

    def __str__(self):
        return f"{self.get_number_display()} ({self.academic_year})"


class Subject(models.Model):
    """
    Subject model with department and additional metadata
    """
    name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='subjects'
    )
    
    description = models.TextField(blank=True, null=True)
    
    # NEW: Additional fields from PostgreSQL schema
    credits = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subjects'
        indexes = [
            models.Index(fields=['subject_code']),
            models.Index(fields=['department', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.subject_code})"


class Course(models.Model):
    """
    NEW: Course model from PostgreSQL schema
    This represents a specific offering of a subject to a class
    (e.g., Python for CSE Year 2 Section A)
    """
    YEAR_CHOICES = [(i, f'Year {i}') for i in range(1, 5)]
    SECTION_CHOICES = [
        ('A', 'Section A'),
        ('B', 'Section B'),
        ('C', 'Section C'),
        ('D', 'Section D'),
    ]
    
    code = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=200)
    
    # Link to subject if you want to maintain relationship
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='courses',
        null=True,
        blank=True
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='courses'
    )
    
    # Class details
    year = models.IntegerField(
        choices=YEAR_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    credits = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1)]
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    
    class Meta:
        db_table = 'courses'
        unique_together = [['code', 'academic_year', 'section']]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['department', 'year', 'section']),
            models.Index(fields=['academic_year', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} (Year {self.year}, Section {self.section})"


class SubjectAllocation(models.Model):
    """
    Enhanced SubjectAllocation with course support
    Assigns a Subject/Course to a Faculty member for a specific Semester
    """
    faculty = models.ForeignKey(
        'profiles.FacultyProfile', 
        on_delete=models.CASCADE, 
        related_name='allocations'
    )
    
    # Keep existing subject field for backward compatibility
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name='allocations',
        null=True,
        blank=True
    )
    
    # NEW: Support for Course model
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='allocations',
        null=True,
        blank=True
    )
    
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    # section=models.ForeignKey(section,on_delete=models.CASCADE)
    
    # NEW: Additional fields
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocations_made',
        limit_choices_to={'user_type__in': ['hod', 'admin']}
    )
    assigned_at = models.DateTimeField(auto_now_add=True,null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'subject_allocations'
        # Updated to handle both subject and course
        unique_together = ('faculty', 'semester')
        indexes = [
            models.Index(fields=['faculty', 'is_active']),
        ]

    def clean(self):
        """Ensure either subject or course is set"""
        if not self.subject and not self.course:
            raise ValidationError('Either subject or course must be set.')

    def __str__(self):
        if self.course:
            return f"{self.course.name} - {self.faculty.user.username} ({self.semester})"
        else:
            return f"{self.subject.name} - {self.faculty.user.username} ({self.semester})"


class CourseEnrollment(models.Model):
    """
    NEW: Links students to courses they're enrolled in
    """
    student = models.ForeignKey(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='course_enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'course_enrollments'
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['student', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} enrolled in {self.course.code}"