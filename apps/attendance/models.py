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
    latitude = models.FloatField(default=12.9716, help_text="Class Location Latitude") 
    longitude = models.FloatField(default=77.5946, help_text="Class Location Longitude")
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