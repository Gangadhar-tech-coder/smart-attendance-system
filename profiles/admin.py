# profiles/admin.py
"""
Admin configuration for profiles with FINAL structure
"""

from django.contrib import admin
from .models import FacultyProfile, StudentProfile, HODProfile


# Inline for Subject Allocations in Faculty Admin
class SubjectAllocationInline(admin.TabularInline):
    """Inline to show and manage subject allocations for faculty"""
    from academics.models import SubjectAllocation
    model = SubjectAllocation
    extra = 1
    fields = ['subject', 'section', 'is_active', 'notes']
    readonly_fields = ['assigned_at']
    verbose_name = "Subject Allocation (Teaching Assignment)"
    verbose_name_plural = "Subject Allocations (Teaching Assignments)"


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    """Faculty Profile Admin"""
    list_display = ['staff_id', 'get_faculty_name', 'department', 'designation', 
                    'get_allocation_count', 'joining_date']
    list_filter = ['department', 'designation', 'joining_date']
    search_fields = ['staff_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email']
    ordering = ['staff_id']
    
    # Add inline for allocations
    inlines = [SubjectAllocationInline]
    
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
    
    def get_allocation_count(self, obj):
        """Show number of active allocations"""
        count = obj.subject_allocations.filter(is_active=True).count()
        return f"{count} subject(s)"
    get_allocation_count.short_description = 'Teaching Load'


# Inline for Course Allocation in Student Admin
class CourseAllocationInline(admin.StackedInline):
    """Inline to show course allocation for student"""
    from academics.models import CourseAllocation
    model = CourseAllocation
    max_num = 1
    can_delete = False
    fields = ['roll_number', 'section', 'academic_year', 'is_active']
    verbose_name = "Course Allocation"
    verbose_name_plural = "Course Allocation"


# Inline for Subject Enrollments in Student Admin
class SubjectEnrollmentInline(admin.TabularInline):
    """Inline to show subject enrollments (for electives)"""
    from academics.models import SubjectEnrollment
    model = SubjectEnrollment
    extra = 1
    fields = ['subject', 'enrolled_at', 'is_active']
    readonly_fields = ['enrolled_at']
    verbose_name = "Subject Enrollment (Elective)"
    verbose_name_plural = "Subject Enrollments (Electives)"


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student Profile Admin"""
    list_display = ['get_roll_number', 'get_student_name', 'get_course_info', 
                    'admission_date']
    list_filter = ['admission_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    ordering = ['user__username']
    
    # Add inlines
    inlines = [CourseAllocationInline, SubjectEnrollmentInline]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Details', {
            'fields': ('admission_date', 'parent_phone', 'address')
        }),
        ('Face Recognition', {
            'fields': ('face_encoding',),
            'classes': ('collapse',),
        }),
    )
    
    def get_roll_number(self, obj):
        """Get roll number from course allocation"""
        if hasattr(obj, 'course_allocation'):
            return obj.course_allocation.roll_number
        return 'Not Allocated'
    get_roll_number.short_description = 'Roll Number'
    
    def get_student_name(self, obj):
        return obj.user.get_full_name()
    get_student_name.short_description = 'Student Name'
    
    def get_course_info(self, obj):
        """Get course information"""
        info = obj.get_course_info()
        if info:
            return f"{info['course']} {info['department']} {info['year']}{info['section']}"
        return 'Not Allocated'
    get_course_info.short_description = 'Course Allocation'


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