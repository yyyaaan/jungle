"""jungle URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django_otp.admin import OTPAdminSite

admin.site.__class__ = OTPAdminSite

urlpatterns = [
    path('', include("frontend.urls")),
    path('cv/', include("yancv.urls")),
    path('ycrawl/', include("ycrawl.urls")),
    path('play/', include("play.urls")),
    path('vision/', include("vision.urls")),
    path('msg/', include("messenger.urls")),
    path('my/', include("webreader.urls")),
    path('admin/', admin.site.urls),
]

# Enforce 2FA only in production.
# if not settings.DEBUG:


