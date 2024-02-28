from django.urls import path, include
from django.contrib.auth.views import LoginView
from userauth.views import logout_view

app_name = 'userauth'

urlpatterns = [
    path("login/",
         LoginView.as_view(
             template_name="userauth/login.html",
             redirect_authenticated_user=True),
             name="login"),
    path("logout/", logout_view, name="logout"),
]