from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from apps.attendance import views as attendance_views
from apps.accounts import views as account_views
from profiles import views as profile_views    
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home & Accounts
    path('', attendance_views.home, name='home'),
    path('signup/', account_views.signup, name='signup'),
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    
    # Teacher Attendance
    path('select_class/', attendance_views.select_class, name='select_class'),
    path('create_session/<int:subject_id>/', attendance_views.create_session, name='create_session'),
    path('monitor_session/<int:session_id>/', attendance_views.monitor_session, name='monitor_session'),
    path('end_session/<int:session_id>/', attendance_views.end_session, name='end_session'),

    # Student Attendance API (Matches your JS fetch call)
    path('api/mark-attendance/', attendance_views.verify_my_face, name='mark_attendance_api'),



    path('reports/', attendance_views.view_reports, name='view_reports'),
    path('reports/<int:session_id>/', attendance_views.session_details, name='session_details'),


    path('attendance/calculator/', attendance_views.attendance_calculator, name='attendance_calculator'),
path('attendance/download-excel/', attendance_views.download_attendance_excel, name='download_attendance_excel'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)