from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_resume, name="upload_resume"),
    path("ats-checker/", views.ats_checker_view, name="ats_checker"),
]
