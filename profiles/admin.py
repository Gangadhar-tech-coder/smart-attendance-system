# profiles/admin.py
"""
Admin configuration for profiles app
"""

from django.contrib import admin
from .models import FacultyProfile, StudentProfile, HODProfile


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    """Faculty Profile Admin"""
    list_display = ['staff_id', 'get_faculty_name', 'department', 'designation', 'joining_date']
    list_filter = ['department', 'designation', 'joining_date']
    search_fields = ['staff_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email']
    ordering = ['staff_id']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'staff_id')
        }),
        ('Department & Position', {
            'fields': ('department', 'designation')
        }),
        ('Professional Details', {
            'fields': ('joining_date', 'qualification', 'specialization')
        }),
    )
    
    def get_faculty_name(self, obj):
        return obj.user.get_full_name()
    get_faculty_name.short_description = 'Faculty Name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'department')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student Profile Admin"""
    list_display = ['roll_number', 'get_student_name', 'department', 'academic_year', 'year', 'section']
    list_filter = ['department', 'academic_year', 'year', 'section']
    search_fields = ['roll_number', 'user__username', 'user__first_name', 'user__last_name', 'user__email']
    ordering = ['roll_number']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'roll_number')
        }),
        ('Academic Information', {
            'fields': ('department', 'academic_year', 'current_semester', 'year', 'section')
        }),
        ('Personal Details', {
            'fields': ('admission_date', 'parent_phone', 'address')
        }),
        ('Face Recognition', {
            'fields': ('face_encoding',),
            'classes': ('collapse',),
        }),
    )
    
    def get_student_name(self, obj):
        return obj.user.get_full_name()
    get_student_name.short_description = 'Student Name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'department', 'academic_year', 'current_semester')


@admin.register(HODProfile)
class HODProfileAdmin(admin.ModelAdmin):
    """HOD Profile Admin"""
    list_display = ['get_hod_name', 'get_department', 'appointment_date']
    list_filter = ['appointment_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['-appointment_date']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('HOD Details', {
            'fields': ('appointment_date', 'responsibilities')
        }),
    )
    
    def get_hod_name(self, obj):
        return obj.user.get_full_name()
    get_hod_name.short_description = 'HOD Name'
    
    def get_department(self, obj):
        dept = obj.get_department()
        return dept.name if dept else 'Not Assigned'
    get_department.short_description = 'Department'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')