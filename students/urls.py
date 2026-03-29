from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="student.index"),
    path('add', views.add_student_view, name="student.add"),
    path('<str:student_id>/view', views.view_student, name="student.view"),
    path('<str:student_id>/edit', views.edit_student_view, name="student.edit"),
    path('<str:student_id>/delete', views.delete_student_view, name="student.delete"),
    path('<str:student_id>/entrance_qr', views.get_entrance_qr_view, name="student.entrance_qr"),
    path('bulk-qr', views.bulk_qr_view, name="student.bulk-qrs"),
]