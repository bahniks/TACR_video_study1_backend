from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.manager, name = 'base'),
    #path('admin/', admin.site.urls),
    path("start_session/", views.startSession, name = "start_session"),
    path("open_session/", views.openSession, name = "open_session"),
    path("close_session/", views.closeSession, name = "close_session"),
    path("end_session/", views.endSession, name = "end_session"),
    path("administrace/", views.administration, name = "administration"),
]
