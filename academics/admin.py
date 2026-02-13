# academics/admin.py
"""
Admin configuration for academics app
"""

from django.contrib import admin
from .models import (
    Department, AcademicYear, Semester, Subject, 
    Course, SubjectAllocation, CourseEnrollment
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Department Admin"""
    list_display = ['code', 'name', 'hod', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'hod__username']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Management', {
            'fields': ('hod', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('hod')


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """Academic Year Admin"""
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'is_current']
    list_filter = ['is_active', 'is_current', 'start_date']
    search_fields = ['name']
    ordering = ['-start_date']
    
    fieldsets = (
        ('Year Information', {
            'fields': ('name', 'start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_current')
        }),
    )


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    """Semester Admin"""
    list_display = ['get_semester_display', 'academic_year', 'start_date', 'end_date', 'is_active']
    list_filter = ['academic_year', 'number', 'is_active']
    search_fields = ['academic_year__name']
    ordering = ['-academic_year', 'number']
    
    def get_semester_display(self, obj):
        return str(obj)
    get_semester_display.short_description = 'Semester'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('academic_year')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Subject Admin"""
    list_display = ['subject_code', 'name', 'department', 'credits', 'is_active']
    list_filter = ['department', 'is_active', 'credits']
    search_fields = ['name', 'subject_code', 'department__name']
    ordering = ['subject_code']
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('name', 'subject_code', 'department')
        }),
        ('Details', {
            'fields': ('description', 'credits', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('department')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Course Admin"""
    list_display = ['code', 'name', 'department', 'academic_year', 'year', 'section', 'credits', 'is_active']
    list_filter = ['department', 'academic_year', 'year', 'section', 'is_active']
    search_fields = ['code', 'name', 'department__name']
    ordering = ['code']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('code', 'name', 'subject')
        }),
        ('Academic Details', {
            'fields': ('department', 'academic_year', 'year', 'section')
        }),
        ('Additional Information', {
            'fields': ('credits', 'description', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('department', 'academic_year', 'subject')


@admin.register(SubjectAllocation)
class SubjectAllocationAdmin(admin.ModelAdmin):
    """Subject Allocation Admin"""
    list_display = ['get_subject_or_course', 'faculty', 'semester', 'is_active', 'assigned_at']
    list_filter = ['is_active', 'assigned_at', 'semester']
    search_fields = ['faculty__user__username', 'subject__name', 'course__name']
    ordering = ['-assigned_at']
    
    fieldsets = (
        ('Allocation Details', {
            'fields': ('faculty', 'subject', 'course', 'semester')
        }),
        ('Management', {
            'fields': ('assigned_by', 'is_active', 'notes')
        }),
    )
    
    def get_subject_or_course(self, obj):
        if obj.course:
            return obj.course.name
        elif obj.subject:
            return obj.subject.name
        return 'N/A'
    get_subject_or_course.short_description = 'Subject/Course'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('faculty__user', 'subject', 'course', 'semester', 'assigned_by')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Course Enrollment Admin"""
    list_display = ['student', 'course', 'enrolled_at', 'is_active']
    list_filter = ['is_active', 'enrolled_at', 'course__department']
    search_fields = ['student__roll_number', 'student__user__username', 'course__code', 'course__name']
    ordering = ['-enrolled_at']
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student__user', 'course')