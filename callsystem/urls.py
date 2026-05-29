from django.urls import path

from . import views

app_name = "callsystem"

urlpatterns = [
    path("", views.call_list, name="call_list"),
    path("clear-cache/", views.clear_cache, name="clear_cache"),
]
