"""
Authentication app URL configuration.

Includes authentication endpoints (register, login, token refresh) and
account management endpoints (username, email, password, deletion).
"""

from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    # Authentication endpoints
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshTokenView.as_view(), name="refresh"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("verify/", views.VerifyCodeView.as_view(), name="verify"),

    # Account management endpoints
    path("account/", views.AccountRetrieveAPIView.as_view(), name="account-retrieve"),
    path("account/update/", views.AccountUpdateAPIView.as_view(), name="account-update"),
    path("account/change-email/", views.EmailChangeRequestAPIView.as_view(), name="email-change"),
    path("account/confirm-email/", views.EmailConfirmAPIView.as_view(), name="email-confirm"),
    path("account/password-change/", views.PasswordChangeAPIView.as_view(), name="password-change"),
    path("account/delete/", views.AccountDeletionRequestAPIView.as_view(), name="account-delete"),
    path("account/confirm-delete/", views.AccountDeletionConfirmAPIView.as_view(), name="account-delete-confirm"),
    path("account/validate-username/", views.UsernameValidationAPIView.as_view(), name="username-validate"),
]
