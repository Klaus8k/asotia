from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm


app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("cabinet/", views.cabinet, name="cabinet"),
    path("profile/", views.profile_edit, name="profile_edit"),
]
