from django.urls import path

from . import views

app_name = "webreader"
urlpatterns = [
    path('', views.myweb, name='index'),
]