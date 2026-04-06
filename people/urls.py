from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="people.index"),
    path('add', views.add_person_view, name="people.add"),
    path('<str:id>/view', views.view_person, name="people.view"),
    path('<str:id>/edit', views.edit_person_view, name="people.edit"),
    path('<str:id>/delete', views.delete_person, name="people.delete"),
    path('<str:id>/entrance_qr', views.get_entrance_qr_view, name="people.entrance_qr"),
    path('bulk-qr', views.bulk_qr_view, name="people.bulk-qrs"),
]