from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.manager, name = 'base'),
    path('results/', views.results, name='results'),
    path('delete_data/', views.deleteData, name='delete_data'),
    path('clear_database/', views.delete, name='delete_database'),
    path("administrace/", views.administration, name = "administration"),
    path("download_data/", views.download, name = "download_data"),
    path("download_all/", views.downloadAll, name = "download_all"),
]
