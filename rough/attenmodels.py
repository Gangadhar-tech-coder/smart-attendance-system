# attendance/models.py
"""
FINAL Attendance models for SubjectAllocation-based structure
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class AttendanceSession(models.Model):
    """
    Attendance Session linked to SubjectAllocation
    Faculty creates session for their assigned Subject-Section combination
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
    
    # IMPORTANT: Link to SubjectAllocation (contains Subject + Section)
    subject_allocation = models.ForeignKey(
        'academics.SubjectAllocation',
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        help_text="Faculty's subject-section allocation"
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
    topic = models.CharField(max_length=200, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    # Location Constraints
    latitude = models.FloatField(default=17.4468, help_text="Class latitude") 
    longitude = models.FloatField(default=78.4468, help_text="Class longitude")
    radius_meters = models.IntegerField(default=20000, help_text="Allowed radius in meters")
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_sessions'
        indexes = [
            models.Index(fields=['is_active', 'session_date']),
            models.Index(fields=['teacher', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['teacher'],
                condition=models.Q(is_active=True),
                name='one_active_session_per_teacher'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.session_code:
            import uuid
            self.session_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_allocation.subject.name} - {self.subject_allocation.section.full_name} ({self.session_date})"
    
    @property
    def subject(self):
        """Get subject from allocation"""
        return self.subject_allocation.subject
    
    @property
    def section(self):
        """Get section from allocation"""
        return self.subject_allocation.section
    
    def get_attendance_count(self):
        """Get attendance statistics"""
        records = self.records.all()
        return {
            'total': records.count(),
            'present': records.filter(status='present').count(),
            'absent': records.filter(status='absent').count(),
            'late': records.filter(status='late').count(),
            'pending': records.filter(status='PENDING').count(),
        }
    
    def end_session(self):
        """End the session"""
        self.end_time = timezone.now()
        self.is_active = False
        self.save()


class AttendanceRecord(models.Model):
    """
    Individual attendance record for a student in a session
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Face Recognition & Image
    captured_image = models.ImageField(upload_to='attendance_captures/', null=True, blank=True)
    verification_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # GPS/Location
    gps_lat = models.FloatField(null=True, blank=True)
    gps_long = models.FloatField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    marked_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_records'
        unique_together = ['session', 'student']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['session', 'student']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.get_status_display()}"
    
    def verify_location(self):
        """Verify if student is within allowed location"""
        if not self.gps_lat or not self.gps_long:
            return False, None
        
        from math import radians, sin, cos, sqrt, atan2
        R = 6371000  # Earth radius in meters
        
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
        """Auto-verify based on score, location, time"""
        issues = []
        
        if self.verification_score and self.verification_score < 70:
            issues.append("Low face recognition score")
        
        is_location_valid, distance = self.verify_location()
        if not is_location_valid and distance:
            issues.append(f"Outside location (distance: {distance:.0f}m)")
        
        time_diff = (self.marked_at - self.session.start_time).total_seconds() / 60
        if time_diff > 15:
            self.status = 'late'
            issues.append("Marked late")
        elif time_diff > 10:
            self.status = 'late'
        
        if not issues:
            self.status = 'present'
        
        self.save()
        return issues


class Permission(models.Model):
    """Student leave/permission requests"""
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
    permission_type = models.CharField(max_length=10, choices=PERMISSION_TYPE_CHOICES)
    reason = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permissions_granted'
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_permissions'
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number if hasattr(self.student, 'course_allocation') else self.student.user.username} - {self.get_permission_type_display()}"