from django.urls import path
from . import views

app_name = "school"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.user_login, name="user_login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("submit-application/", views.submit_application, name="submit_application"),
    path("check-status/", views.application_status, name="check_status"),
    path("application-status/", views.application_status, name="application_status"),
    path("submit-feedback/", views.submit_feedback, name="submit_feedback"),
    path("feedback/", views.submit_feedback, name="feedback"),
    path("library/<int:book_id>/download/", views.download_book, name="download_book"),
]
