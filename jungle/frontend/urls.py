from django.urls import path

from . import views

app_name = "frontend"
urlpatterns = [
    path('', views.hello, name='index'),
    path('sitemap/', views.get_urls, name="site-url"),
    path('vms/', views.vm_management, name='vms'),
    path('overview/', views.job_overview, name="overview"),
    path('overview/log/', views.job_overview_log, name="overview-log"),
    path('overview/vmplot/', views.job_overview_vmplot, name="overview-vmplot"),
]
