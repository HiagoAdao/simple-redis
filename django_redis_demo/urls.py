from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("callsystem:call_list")),
    path("calls/", include("callsystem.urls", namespace="callsystem")),
]
