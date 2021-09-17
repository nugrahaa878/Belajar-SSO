from django.contrib import admin
from django.urls import path
from .cas_wrappers import APILoginView, APILogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("login/", APILoginView.as_view(), name="login"),
]
