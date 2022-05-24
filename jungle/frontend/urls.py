from django.urls import path

from . import views

app_name = "frontend"
urlpatterns = [
    path('', views.hello, name='index'),
    path('sitemap/', views.get_urls, name="site-url"),
    path('vms/', views.vm_management, name='vms'),
    path('vmaction/', views.vm_action, name="vmaction"),
]