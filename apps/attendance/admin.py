# attendance/admin.py
"""
Admin configuration for attendance app
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceSession, AttendanceRecord, Permission


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    """Attendance Session Admin"""
    list_display = [
        'session_code', 
        'get_teacher_name', 
        'get_subject_or_course', 
        'session_date', 
        'session_type',
        'is_active_badge',
        'start_time'
    ]
    list_filter = ['is_active', 'session_type', 'session_date', 'teacher']
    search_fields = [
        'session_code', 
        'teacher__username', 
        'subject__name', 
        'course__name'
    ]
    ordering = ['-session_date', '-start_time']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('teacher', 'subject', 'course', 'allocation')
        }),
        ('Schedule', {
            'fields': ('session_date', 'start_time', 'end_time', 'session_type')
        }),
        ('Status & Code', {
            'fields': ('session_code', 'is_active', 'remarks')
        }),
        ('Location Settings', {
            'fields': ('latitude', 'longitude', 'radius_meters'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['session_code']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name()
    get_teacher_name.short_description = 'Teacher'
    
    def get_subject_or_course(self, obj):
        if obj.course:
            return obj.course.name
        elif obj.subject:
            return obj.subject.name
        return 'N/A'
    get_subject_or_course.short_description = 'Subject/Course'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: gray;">○ Ended</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('teacher', 'subject', 'course', 'allocation')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Attendance Record Admin"""
    list_display = [
        'get_student_name',
        'get_session_info',
        'status_badge',
        'verification_score',
        'marked_at',
        'location_verified'
    ]
    list_filter = ['status', 'marked_at', 'session__session_date', 'session__subject']
    search_fields = [
        'student__username',
        'student__first_name',
        'student__last_name',
        'session__session_code'
    ]
    ordering = ['-marked_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session', 'student', 'status')
        }),
        ('Verification Data', {
            'fields': ('captured_image', 'verification_score')
        }),
        ('Location Data', {
            'fields': ('gps_lat', 'gps_long', 'ip_address', 'device_info')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'marked_at')
        }),
    )
    
    readonly_fields = ['timestamp']
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()
    get_student_name.short_description = 'Student'
    
    def get_session_info(self, obj):
        subject = obj.session.course.name if obj.session.course else (
            obj.session.subject.name if obj.session.subject else 'N/A'
        )
        return f"{subject} - {obj.session.session_date}"
    get_session_info.short_description = 'Session'
    
    def status_badge(self, obj):
        colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'PENDING': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def location_verified(self, obj):
        if obj.gps_lat and obj.gps_long:
            is_valid, distance = obj.verify_location()
            if is_valid:
                return format_html(
                    '<span style="color: green;">✓ Valid ({:.0f}m)</span>',
                    distance
                )
            else:
                return format_html(
                    '<span style="color: red;">✗ Invalid ({:.0f}m)</span>',
                    distance
                )
        return format_html('<span style="color: gray;">No GPS data</span>')
    location_verified.short_description = 'Location'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'session__subject', 'session__course')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Permission Admin"""
    list_display = [
        'get_student_info',
        'permission_type',
        'date',
        'time_range',
        'status_badge',
        'get_granted_by'
    ]
    list_filter = ['status', 'permission_type', 'date', 'created_at']
    search_fields = [
        'student__roll_number',
        'student__user__username',
        'reason'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Permission Details', {
            'fields': ('permission_type', 'reason', 'date', 'start_time', 'end_time')
        }),
        ('Approval', {
            'fields': ('status', 'granted_by', 'remarks')
        }),
    )
    
    def get_student_info(self, obj):
        return f"{obj.student.roll_number} - {obj.student.user.get_full_name()}"
    get_student_info.short_description = 'Student'
    
    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = 'Time'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_granted_by(self, obj):
        if obj.granted_by:
            return obj.granted_by.get_full_name()
        return '-'
    get_granted_by.short_description = 'Approved By'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student__user', 'granted_by')
    
    # Custom actions
    actions = ['approve_permissions', 'reject_permissions']
    
    def approve_permissions(self, request, queryset):
        queryset.filter(status='PENDING').update(
            status='APPROVED',
            granted_by=request.user
        )
        self.message_user(request, f"{queryset.count()} permissions approved.")
    approve_permissions.short_description = "Approve selected permissions"
    
    def reject_permissions(self, request, queryset):
        queryset.filter(status='PENDING').update(
            status='REJECTED',
            granted_by=request.user
        )
        self.message_user(request, f"{queryset.count()} permissions rejected.")
    reject_permissions.short_description = "Reject selected permissions"