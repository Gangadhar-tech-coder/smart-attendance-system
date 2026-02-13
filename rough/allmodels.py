#  academics/models.py
from django.db import models
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="e.g., CSE, ECE, MECH")
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name
class AcademicYear(models.Model):
    name = models.CharField(max_length=20, help_text="e.g., 2023-2024")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False, help_text="Check this if this is the current academic year")
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        # Ensure only one academic year is active at a time
        if self.is_active:
            AcademicYear.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
class Semester(models.Model):
    # Linking semester to a specific academic year allows you to track history (e.g., Sem 1 of 2023 vs Sem 1 of 2024)
    SEMESTER_CHOICES = [
        (1, 'Semester 1'), (2, 'Semester 2'), (3, 'Semester 3'),
        (4, 'Semester 4'), (5, 'Semester 5'), (6, 'Semester 6'),
        (7, 'Semester 7'), (8, 'Semester 8'),
    ]
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    number = models.IntegerField(choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('academic_year', 'number') # Prevents duplicate Sem 1s in the same year

    def __str__(self):
        return f"{self.get_number_display()} ({self.academic_year})"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.subject_code})"

class SubjectAllocation(models.Model):
    """
    Assigns a Subject to a Faculty member for a specific Semester.
    Example: Prof. Smith teaches 'Python' to 'Semester 1'
    """
    # We use a string reference 'profiles.FacultyProfile' to avoid circular import errors
    faculty = models.ForeignKey('profiles.FacultyProfile', on_delete=models.CASCADE, related_name='allocations')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='allocations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    
    class Meta:
        # Ensures a teacher isn't assigned the same subject twice for the same class
        unique_together = ('faculty', 'subject', 'semester')

    def __str__(self):
        return f"{self.subject.name} - {self.faculty.user.username} ({self.semester})"

# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # --- ROLES ---
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    
    # --- PERSONAL INFO ---
    phone_number = models.CharField(max_length=15, blank=True)
    
    # --- ACADEMIC INFO (For Students) ---
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True, help_text="Roll Number")
    department = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. CSE, ECE")

    # --- FACE RECOGNITION DATA (For Smart Attendance) ---
    # Stores the photo of the student
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    reference_image = models.ImageField(upload_to='security_references/', blank=True, null=True)
    # Stores the mathematical representation of the face for AI comparison
    face_encoding = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"

# --- SUBJECT MODEL (For Staff) ---
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    staff = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'staff'},
        related_name='subjects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

#  attendance/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import Subject 

class AttendanceSession(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'staff'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    session_code = models.CharField(max_length=10, unique=True, blank=True)

    # --- NEW: Location Constraints ---
    # Default to a specific location (e.g., College Campus coordinates)
    # You can change these defaults to your actual college location
    latitude = models.FloatField(default=17.4468, help_text="Class Location Latitude") 
    longitude = models.FloatField(default=78.4468, help_text="Class Location Longitude")
    radius_meters = models.IntegerField(default=200, help_text="Allowed radius in meters")

    def save(self, *args, **kwargs):
        if not self.session_code:
            import uuid
            self.session_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('PENDING', 'Pending Verification'), # Added Pending status for safety
    ]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # --- NEW FIELDS ADDED HERE ---
    captured_image = models.ImageField(upload_to='attendance_captures/', null=True, blank=True)
    gps_lat = models.FloatField(null=True, blank=True)
    gps_long = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ['session', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.status}"

#  profiles/models.py
from django.db import models
from django.conf import settings  # <--- vital change
from academics.models import Department, AcademicYear, Semester

class FacultyProfile(models.Model):
    # We use settings.AUTH_USER_MODEL instead of importing User directly
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    staff_id = models.CharField(max_length=20, unique=True)
 
    def __str__(self):
        return f"{self.user} - {self.staff_id}"

class StudentProfile(models.Model):
    # We use settings.AUTH_USER_MODEL here too
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    current_semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    roll_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.roll_number} - {self.user}"   


