from django.urls import path

from . import views

app_name = "yancv"
urlpatterns = [
    path('', views.cv, name='index'),
]