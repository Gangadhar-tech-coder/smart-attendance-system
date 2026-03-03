# academics/admin.py
"""
Admin configuration for FINAL academic structure
"""

from django.contrib import admin
from .models import (
    Department, AcademicYear, Course, CourseDepartment, Semester,
    Subject, Section, CourseAllocation, SubjectAllocation, SubjectEnrollment
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


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """Academic Year Admin"""
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'is_current']
    list_filter = ['is_active', 'is_current', 'start_date']
    search_fields = ['name']
    ordering = ['-start_date']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Course (BTech, MTech, PhD) Admin"""
    list_display = ['short_name', 'name', 'course_type', 'duration_years', 'total_semesters', 'is_active']
    list_filter = ['course_type', 'is_active']
    search_fields = ['name', 'short_name']
    ordering = ['short_name']


@admin.register(CourseDepartment)
class CourseDepartmentAdmin(admin.ModelAdmin):
    """Course-Department Links Admin"""
    list_display = ['course', 'department', 'is_active', 'created_at']
    list_filter = ['course', 'department', 'is_active']
    search_fields = ['course__short_name', 'department__code']
    ordering = ['course', 'department']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    """Semester Admin"""
    list_display = ['get_semester_name', 'course', 'academic_year', 'semester_number', 'is_active']
    list_filter = ['course', 'academic_year', 'is_active']
    search_fields = ['course__short_name', 'academic_year__name']
    ordering = ['academic_year', 'course', 'semester_number']
    
    def get_semester_name(self, obj):
        return str(obj)
    get_semester_name.short_description = 'Semester'


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """Section Admin"""
    list_display = ['get_section_name', 'course_department', 'year', 'section_letter', 'capacity', 'is_active']
    list_filter = ['course_department__course', 'course_department__department', 'year', 'section_letter', 'is_active']
    search_fields = ['course_department__course__short_name', 'course_department__department__code']
    ordering = ['course_department', 'year', 'section_letter']
    
    def get_section_name(self, obj):
        return obj.full_name
    get_section_name.short_description = 'Section'
    
    fieldsets = (
        ('Section Details', {
            'fields': ('course_department', 'academic_year', 'year', 'section_letter')
        }),
        ('Additional Info', {
            'fields': ('current_semester', 'capacity', 'is_active')
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Subject Admin"""
    list_display = ['subject_code', 'name', 'course', 'department', 'semester', 'credits', 'is_elective', 'is_active']
    list_filter = ['course', 'department', 'semester', 'is_elective', 'is_active']
    search_fields = ['name', 'subject_code']
    ordering = ['subject_code']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'subject_code')
        }),
        ('Classification', {
            'fields': ('course', 'department', 'semester')
        }),
        ('Details', {
            'fields': ('credits', 'description', 'is_elective', 'is_active')
        }),
    )


@admin.register(CourseAllocation)
class CourseAllocationAdmin(admin.ModelAdmin):
    """Course Allocation (Student Enrollment) Admin"""
    list_display = ['roll_number', 'get_student_name', 'get_section_name', 'academic_year', 'is_active']
    list_filter = ['section__course_department__course', 'section__course_department__department', 
                   'section__year', 'academic_year', 'is_active']
    search_fields = ['roll_number', 'student__user__username', 'student__user__first_name', 
                     'student__user__last_name']
    ordering = ['roll_number']
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student Name'
    
    def get_section_name(self, obj):
        return obj.section.full_name
    get_section_name.short_description = 'Section'
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'roll_number')
        }),
        ('Allocation Details', {
            'fields': ('section', 'academic_year', 'is_active')
        }),
    )


@admin.register(SubjectAllocation)
class SubjectAllocationAdmin(admin.ModelAdmin):
    """Subject Allocation (Teaching Assignment) Admin"""
    list_display = ['get_faculty_name', 'get_subject_name', 'get_section_name', 'is_active', 'assigned_at']
    list_filter = ['section__course_department__course', 'section__course_department__department', 
                   'is_active', 'assigned_at']
    search_fields = ['faculty__user__username', 'faculty__staff_id', 'subject__name', 'subject__subject_code']
    ordering = ['-assigned_at']
    
    def get_faculty_name(self, obj):
        return f"{obj.faculty.staff_id} - {obj.faculty.user.get_full_name()}"
    get_faculty_name.short_description = 'Faculty'
    
    def get_subject_name(self, obj):
        return f"{obj.subject.subject_code} - {obj.subject.name}"
    get_subject_name.short_description = 'Subject'
    
    def get_section_name(self, obj):
        return obj.section.full_name
    get_section_name.short_description = 'Section'
    
    fieldsets = (
        ('Allocation', {
            'fields': ('faculty', 'subject', 'section')
        }),
        ('Management', {
            'fields': ('assigned_by', 'is_active', 'notes')
        }),
    )


@admin.register(SubjectEnrollment)
class SubjectEnrollmentAdmin(admin.ModelAdmin):
    """Subject Enrollment (for electives) Admin"""
    list_display = ['get_student_roll', 'get_subject_name', 'enrolled_at', 'is_active']
    list_filter = ['subject__course', 'subject__department', 'is_active', 'enrolled_at']
    search_fields = ['student__user__username', 'subject__name', 'subject__subject_code']
    ordering = ['-enrolled_at']
    
    def get_student_roll(self, obj):
        if hasattr(obj.student, 'course_allocation'):
            return obj.student.course_allocation.roll_number
        return obj.student.user.username
    get_student_roll.short_description = 'Student'
    
    def get_subject_name(self, obj):
        return f"{obj.subject.subject_code} - {obj.subject.name}"
    get_subject_name.short_description = 'Subject'