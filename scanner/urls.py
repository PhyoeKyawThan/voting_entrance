from django.urls import path
from . import views
urlpatterns = [
    path("", views.index, name="scanner.index"),
    path("scan", views.qr_scan, name="scanner.scan"),
    path("arduino-status", views.arduino_status, name="scanner.arduino_status"),
]