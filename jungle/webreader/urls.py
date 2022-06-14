from django.urls import path

from . import views

app_name = "webreader"
urlpatterns = [
    path('', views.myweb, name='index'),
    path('update/', views.update_results, name='update'),
    path('do/', views.start_multi_webs, name="perform web reading"),
]