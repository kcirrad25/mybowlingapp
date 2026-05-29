from django.contrib.auth import views as auth_views
from django.urls import path

from .views import admin_mfa_setup_view, admin_mfa_verify_view, profile_view, request_access_view, signup_view

app_name = "accounts"

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", profile_view, name="profile"),
    path("request-access/", request_access_view, name="request_access"),
    path("admin-mfa/setup/", admin_mfa_setup_view, name="admin_mfa_setup"),
    path("admin-mfa/verify/", admin_mfa_verify_view, name="admin_mfa_verify"),
]
