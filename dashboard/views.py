from django.shortcuts import render
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request: HttpRequest):
    return render(request, 'dashboard/index.html')