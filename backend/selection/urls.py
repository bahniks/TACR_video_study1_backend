from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.manager, name = 'base'),
    path('results/', views.results, name='results'),
    path('delete_data/', views.deleteData, name='delete_data'),
    path('clear_database/', views.delete, name='delete_database'),
    path("start_session/", views.startSession, name = "start_session"),
    path("open_session/", views.openSession, name = "open_session"),
    path("close_session/", views.closeSession, name = "close_session"),
    path("end_session/", views.endSession, name = "end_session"),
    path("administrace/", views.administration, name = "administration"),
    path("download_data/", views.download, name = "download_data"),
]
