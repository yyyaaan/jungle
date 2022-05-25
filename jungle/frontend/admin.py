from django.contrib import admin
from .models import *

class AdminSiteUrl(admin.ModelAdmin):
    list_display = ("cleanurl", "menu1", "menu2", "menu3", "desc1", "desc2", "desc3", "icon", "style")
    ordering = ("menu1", "menu2")
    

admin.site.register(SiteUrl, AdminSiteUrl)