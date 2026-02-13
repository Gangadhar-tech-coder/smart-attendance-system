# attendance/models.py
"""
Enhanced Attendance models integrating PostgreSQL schema features
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class AttendanceSession(models.Model):
    """
    Enhanced Attendance Session with location tracking and verification
    """
    SESSION_TYPE_CHOICES = [
        ('LECTURE', 'Lecture'),
        ('LAB', 'Laboratory'),
        ('TUTORIAL', 'Tutorial'),
        ('PRACTICAL', 'Practical'),
    ]
    
    # Teacher/Faculty
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type__in': ['staff', 'hod']},
        related_name='started_sessions'
    )
    
    # Subject - Keep for backward compatibility
    subject = models.ForeignKey(
        'accounts.Subject',  # or 'academics.Subject' depending on your choice
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        null=True,
        blank=True
    )
    
    # NEW: Link to course if using Course model
    course = models.ForeignKey(
        'academics.Course',
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        null=True,
        blank=True
    )
    
    # NEW: Link to SubjectAllocation for better tracking
    allocation = models.ForeignKey(
        'academics.SubjectAllocation',
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        blank=True,
        help_text="Links to the faculty's subject allocation"
    )
    
    # Time tracking
    session_date = models.DateField(default=timezone.now)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Session details
    session_code = models.CharField(max_length=10, unique=True, blank=True)
    session_type = models.CharField(
        max_length=10,
        choices=SESSION_TYPE_CHOICES,
        default='LECTURE'
    )
    remarks = models.TextField(blank=True, null=True)

    # --- Location Constraints ---
    latitude = models.FloatField(
        default=17.4468, 
        help_text="Class Location Latitude"
    ) 
    longitude = models.FloatField(
        default=78.4468, 
        help_text="Class Location Longitude"
    )
    radius_meters = models.IntegerField(
        default=200, 
        help_text="Allowed radius in meters"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_sessions'
        indexes = [
            models.Index(fields=['is_active', 'session_date']),
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['session_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['teacher'],
                condition=models.Q(is_active=True),
                name='single_active_session_per_teacher'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.session_code:
            import uuid
            self.session_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate that subject or course is set"""
        if not self.subject and not self.course:
            raise ValidationError('Either subject or course must be set.')
        
        # Ensure only one active session per faculty
        if self.is_active:
            existing = AttendanceSession.objects.filter(
                teacher=self.teacher,
                is_active=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError('Teacher can only have one active session at a time.')

    def __str__(self):
        subject_name = self.course.name if self.course else (self.subject.name if self.subject else 'Unknown')
        return f"{subject_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def get_attendance_count(self):
        """Get attendance statistics for this session"""
        records = self.records.all()
        return {
            'total': records.count(),
            'present': records.filter(status='present').count(),
            'absent': records.filter(status='absent').count(),
            'pending': records.filter(status='PENDING').count(),
        }
    
    def end_session(self):
        """End the session"""
        self.end_time = timezone.now()
        self.is_active = False
        self.save()


class AttendanceRecord(models.Model):
    """
    Enhanced Attendance Record with verification and geolocation
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),  # NEW: Added late status
        ('PENDING', 'Pending Verification'),
    ]

    session = models.ForeignKey(
        AttendanceSession, 
        on_delete=models.CASCADE, 
        related_name='records'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'student'},
        related_name='attendance_records'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )

    # --- Face Recognition & Image Capture ---
    captured_image = models.ImageField(
        upload_to='attendance_captures/', 
        null=True, 
        blank=True
    )
    
    # NEW: Verification score from face recognition
    verification_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Face recognition confidence score (0-100)"
    )
    
    # --- GPS/Location Data ---
    gps_lat = models.FloatField(null=True, blank=True)
    gps_long = models.FloatField(null=True, blank=True)
    
    # NEW: IP and Device tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    
    # NEW: Marked at timestamp (when attendance was marked)
    marked_at = models.DateTimeField(default=timezone.now)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance'
        unique_together = ['session', 'student']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['session', 'student']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.get_status_display()}"
    
    def verify_location(self):
        """
        Verify if student is within allowed location radius
        Returns: (is_valid, distance_meters)
        """
        if not self.gps_lat or not self.gps_long:
            return False, None
        
        from math import radians, sin, cos, sqrt, atan2
        
        # Haversine formula to calculate distance
        R = 6371000  # Earth's radius in meters
        
        lat1 = radians(self.session.latitude)
        lat2 = radians(self.gps_lat)
        delta_lat = radians(self.gps_lat - self.session.latitude)
        delta_lon = radians(self.gps_long - self.session.longitude)
        
        a = sin(delta_lat/2)**2 + cos(lat1) * cos(lat2) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        is_valid = distance <= self.session.radius_meters
        return is_valid, distance
    
    def auto_verify(self):
        """
        Automatically verify attendance based on:
        - Verification score
        - Location
        - Time
        """
        issues = []
        
        # Check verification score
        if self.verification_score and self.verification_score < 70:
            issues.append("Low face recognition score")
        
        # Check location
        is_location_valid, distance = self.verify_location()
        if not is_location_valid:
            issues.append(f"Outside allowed location (distance: {distance:.0f}m)")
        
        # Check time (if late)
        time_diff = (self.marked_at - self.session.start_time).total_seconds() / 60
        if time_diff > 15:
            self.status = 'late'
            issues.append("Marked late")
        elif time_diff > 10:
            self.status = 'late'
        
        # If no issues, mark as present
        if not issues:
            self.status = 'present'
        
        self.save()
        return issues


class Permission(models.Model):
    """
    NEW: Student leave/permission requests
    """
    PERMISSION_TYPE_CHOICES = [
        ('SPORTS', 'Sports Activity'),
        ('OUTDOOR', 'Outdoor Activity'),
        ('EXTRA', 'Extra Curricular'),
        ('MEDICAL', 'Medical Leave'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    student = models.ForeignKey(
        'profiles.StudentProfile',
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    permission_type = models.CharField(
        max_length=10, 
        choices=PERMISSION_TYPE_CHOICES
    )
    reason = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permissions_granted',
        limit_choices_to={'user_type__in': ['hod', 'staff', 'admin']}
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now,null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'permissions'
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        """Validate that end_time is after start_time"""
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.get_permission_type_display()} - {self.get_status_display()}"