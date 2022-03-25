from django.contrib import admin

from .models import *

# Register your models here.

class VmRegistryAdmin(admin.ModelAdmin):
    list_display = ("vmid", "provider","project", "batchnum")
    
class VmTrailAdmin(admin.ModelAdmin):
    list_display = ("vmid", "event", "info", "timestamp")
    list_filter = ["timestamp"]
    

admin.site.register(VmRegistry, VmRegistryAdmin)
admin.site.register(VmTrail, VmTrailAdmin)