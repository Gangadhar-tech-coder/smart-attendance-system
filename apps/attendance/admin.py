from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'teacher', 'start_time', 'is_active')
    list_filter = ('is_active', 'start_time')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'timestamp', 'status')
    list_filter = ('session', 'status')