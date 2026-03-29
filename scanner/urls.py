from django.urls import path
from . import views
urlpatterns = [
    path("", views.index, name="scanner.index"),
    path("scan", views.qr_scan, name="scanner.scan"),
]