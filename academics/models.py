# academics/models.py
"""
FINAL CORRECT STRUCTURE:
- Course = Educational Program (BTech, MTech, PhD)
- Department = Branch (CSE, ECE, AI, VLSI)
- CourseAllocation = Student enrollment in Course+Dept
- Subject = Teaching units
- Section = Course + Department + Year + Section Letter
- SubjectAllocation = Faculty → Subject → Section
"""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings


class Department(models.Model):
    """
    Departments/Branches: CSE, ECE, MECH, AI, VLSI, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=10, 
        unique=True, 
        help_text="e.g., CSE, ECE, MECH, AI, VLSI"
    )
    description = models.TextField(blank=True, null=True)
    
    hod = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department',
        limit_choices_to={'user_type': 'hod'}
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'departments'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicYear(models.Model):
    """
    Academic Year (e.g., 2024-25)
    """
    name = models.CharField(max_length=20, help_text="e.g., 2024-25")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'academic_years'
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class Course(models.Model):
    """
    Educational Programs: BTech, MTech, PhD, etc.
    (Called "Course" to match your terminology)
    """
    COURSE_TYPE_CHOICES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('PhD', 'Doctorate'),
    ]
    
    name = models.CharField(max_length=100, help_text="e.g., Bachelor of Technology")
    short_name = models.CharField(max_length=20, unique=True, help_text="e.g., BTech, MTech, PhD")
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES)
    duration_years = models.IntegerField(help_text="Duration in years")
    total_semesters = models.IntegerField(help_text="Total number of semesters")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'courses'
    
    def __str__(self):
        return f"{self.short_name} - {self.name}"


class CourseDepartment(models.Model):
    """
    Links Courses to Departments
    e.g., BTech has CSE, ECE, MECH
         MTech has AI, VLSI, DS
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_departments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='course_departments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'course_departments'
        unique_together = [['course', 'department']]
    
    def __str__(self):
        return f"{self.course.short_name} - {self.department.code}"


class Semester(models.Model):
    """
    Semesters for each Course
    Different courses have different number of semesters
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(help_text="Semester number (1, 2, 3, etc.)")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = 'semesters'
        unique_together = ('course', 'academic_year', 'semester_number')
    
    def __str__(self):
        return f"{self.course.short_name} - Semester {self.semester_number} ({self.academic_year})"


class Section(models.Model):
    """
    Section = Course + Department + Year + Section Letter
    Example: BTech CSE Year 2 Section A
    This is what students belong to and what faculty teach
    """
    YEAR_CHOICES = [(i, f'Year {i}') for i in range(1, 5)]
    SECTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')]
    
    course_department = models.ForeignKey(
        CourseDepartment,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Which Course-Department combination (e.g., BTech-CSE)"
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    year = models.IntegerField(
        choices=YEAR_CHOICES,
        help_text="Which year of study (1, 2, 3, 4)"
    )
    section_letter = models.CharField(
        max_length=1,
        choices=SECTION_CHOICES,
        help_text="Section letter (A, B, C, D, E)"
    )
    current_semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections'
    )
    capacity = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'sections'
        unique_together = [['course_department', 'academic_year', 'year', 'section_letter']]
    
    def __str__(self):
        return f"{self.course_department.course.short_name} {self.course_department.department.code} Year {self.year} Section {self.section_letter}"
    
    @property
    def full_name(self):
        """Returns: BTech CSE 2A"""
        return f"{self.course_department.course.short_name} {self.course_department.department.code} {self.year}{self.section_letter}"


class Subject(models.Model):
    """
    Subjects: Actual teaching subjects
    Different for each Course + Department + Semester
    Example: "Machine Learning" for MTech AI Semester 1
    """
    name = models.CharField(max_length=200)
    subject_code = models.CharField(max_length=20, unique=True)
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subjects',
        help_text="Which course (BTech/MTech/PhD)"
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='subjects',
        help_text="Which department (CSE/ECE/AI/VLSI)"
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='subjects',
        help_text="Which semester"
    )
    
    credits = models.IntegerField(default=3)
    description = models.TextField(blank=True, null=True)
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        db_table = 'subjects'
    
    def __str__(self):
        return f"{self.subject_code} - {self.name} ({self.course.short_name} {self.department.code} Sem {self.semester.semester_number})"


class CourseAllocation(models.Model):
    """
    Student's enrollment in a Course
    Links: Student → Course + Department + Section
    Example: Student enrolled in BTech CSE Year 2 Section A
    """
    student = models.OneToOneField(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='course_allocation'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name='student_allocations',
        help_text="Which section the student belongs to"
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='course_allocations',
        help_text="Year of admission"
    )
    roll_number = models.CharField(
        max_length=30,
        unique=True,
        help_text="Student roll number"
    )
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'course_allocations'
    
    def __str__(self):
        return f"{self.roll_number} → {self.section.full_name}"
    
    @property
    def course(self):
        """Returns the course (BTech/MTech/PhD)"""
        return self.section.course_department.course
    
    @property
    def department(self):
        """Returns the department (CSE/ECE/AI)"""
        return self.section.course_department.department
    
    @property
    def year(self):
        """Returns current year of study"""
        return self.section.year
    
    @property
    def current_semester(self):
        """Returns current semester"""
        return self.section.current_semester


class SubjectAllocation(models.Model):
    """
    Subject Allocation: Faculty → Subject → Section
    Example: Prof. Smith teaches "Machine Learning" to "MTech AI Year 1 Section A"
    
    This is the TEACHING ASSIGNMENT
    """
    faculty = models.ForeignKey(
        'profiles.FacultyProfile', 
        on_delete=models.CASCADE, 
        related_name='subject_allocations'
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name='allocations'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='subject_allocations',
        help_text="Which section this faculty teaches (Course + Dept + Year + Section)"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocations_made'
    )
    assigned_at = models.DateTimeField(auto_now_add=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'subject_allocations'
        unique_together = [['faculty', 'subject', 'section']]
    
    def __str__(self):
        return f"{self.faculty.user.get_full_name()} → {self.subject.name} → {self.section.full_name}"
    
    def clean(self):
        """Validate that subject matches section"""
        if self.subject.course != self.section.course_department.course:
            raise ValidationError(
                f"Subject is for {self.subject.course.short_name} but section is for {self.section.course_department.course.short_name}"
            )
        if self.subject.department != self.section.course_department.department:
            raise ValidationError(
                f"Subject is for {self.subject.department.code} but section is for {self.section.course_department.department.code}"
            )


class SubjectEnrollment(models.Model):
    """
    Optional: For elective subjects
    Links specific students to specific subjects
    """
    student = models.ForeignKey(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='subject_enrollments'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'subject_enrollments'
        unique_together = [['student', 'subject']]
    
    def __str__(self):
        return f"{self.student.roll_number} enrolled in {self.subject.subject_code}"