from django.contrib import admin
from .models import FacultyProfile, StudentProfile

@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    # This controls what columns you see in the list
    list_display = ('user', 'staff_id', 'department')
    # This adds a search bar
    search_fields = ('user__username', 'staff_id')
    # This adds a filter sidebar
    list_filter = ('department',)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'department', 'current_semester')
    search_fields = ('user__username', 'roll_number')
    list_filter = ('department', 'current_semester', 'academic_year')