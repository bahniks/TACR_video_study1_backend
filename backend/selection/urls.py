from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.manager, name = 'base'),
    #path('admin/', admin.site.urls),
    path("start_session/", views.startSession, name = "start_session"),
    path("open_session/", views.openSession, name = "open_session"),
    path("session_info/", views.sessionInfo, name = "session_info"),
]
