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
    
    # Optional: If a subject is strictly tied to a specific semester instance (e.g., Sem 1 2024)
    # create a linking model later. For now, we can link it generically or specifically.
    # Approach: A subject usually belongs to a Department. Assignment to a semester happens in Class/Schedule.
    # However, for simple curriculum structures, we can link it to a generic semester number or the active semester.
    
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.subject_code})"
    



    # ... (Your existing imports)

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