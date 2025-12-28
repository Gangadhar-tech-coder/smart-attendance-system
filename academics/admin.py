from django.contrib import admin
from .models import Department, AcademicYear, Semester, Subject , SubjectAllocation

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('number', 'academic_year', 'start_date', 'end_date')
    list_filter = ('academic_year',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_code', 'department')
    list_filter = ('department',)


@admin.register(SubjectAllocation)
class SubjectAllocationAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'subject', 'semester')
    list_filter = ('semester', 'faculty')
    search_fields = ('subject__name', 'faculty__user__username')