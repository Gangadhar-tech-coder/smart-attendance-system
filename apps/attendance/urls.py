from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('select-class/', views.select_class, name='select_class'),
    path('create-session/<int:allocation_id>/', views.create_session, name='create_session'),
    path('monitor/<int:session_id>/', views.monitor_session, name='monitor_session'),
    path('end-session/<int:session_id>/', views.end_session, name='end_session'),
    path('reports/', views.view_reports, name='view_reports'),
    path('reports/<int:session_id>/', views.session_details, name='session_details'),
    path('calculator/', views.attendance_calculator, name='attendance_calculator'),
    path('download-excel/', views.download_attendance_excel, name='download_excel'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('api/verify-face/', views.verify_my_face, name='verify_face'),
]