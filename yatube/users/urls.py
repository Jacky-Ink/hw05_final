from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('signup/',
         views.SignUp.as_view(), name='signup'
         ),
    path('logged_out/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logged_out'
         ),
    path('login/',
         LoginView.as_view(template_name='users/login.html'),
         name='login'
         ),
    path('password_change/', PasswordChangeView.as_view(
        template_name='users/password_change_form.html'),
        name='password_change_form')
]
