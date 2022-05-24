from django.contrib import admin
from .models import *

class AdminSiteUrl(admin.ModelAdmin):
    list_display = ("rawurl", "cleanurl", "menu1", "menu2", "desc1", "desc2", "icon")
    ordering = ("menu1", "menu2")
    

admin.site.register(SiteUrl, AdminSiteUrl)