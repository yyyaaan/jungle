from django.contrib import admin

from .models import *

class VisionDBAdmin(admin.ModelAdmin):
    list_display = ("userdesc", "outjson", "timestamp")
    list_filter = ["timestamp"]
    

admin.site.register(VisionDB, VisionDBAdmin)