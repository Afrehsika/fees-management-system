from django.urls import path
from .views import LoginView,View_logout

urlpatterns = [
    path("login",LoginView.as_view(), name="login"),
    path("logout",View_logout,name="logout")
]
