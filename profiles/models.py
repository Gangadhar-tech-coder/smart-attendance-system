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