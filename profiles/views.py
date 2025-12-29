from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def student_dashboard(request):
    return render(request, 'student_dashboard.html')