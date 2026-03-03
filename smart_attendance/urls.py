from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from apps.attendance import views as attendance_views
from apps.accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', attendance_views.home, name='home'),

    # Accounts
    path('signup/', account_views.signup, name='signup'),
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('dashboard/', account_views.dashboard_redirect, name='dashboard'),
    path('dashboard/student/', account_views.student_dashboard, name='student_dashboard'),
    path('dashboard/faculty/', account_views.faculty_dashboard, name='faculty_dashboard'),
    path('api/mark-attendance/', attendance_views.verify_my_face, name='mark_attendance_api'),

    # ✅ ALL attendance URLs - uses attendance/urls.py which has app_name = 'attendance'
    path('attendance/', include('apps.attendance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)