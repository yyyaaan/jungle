from django.contrib import admin

from .models import *

# Register your models here.

class VmRegistryAdmin(admin.ModelAdmin):
    list_display = ("vmid", "provider","project", "batchnum")
    
class VmTrailAdmin(admin.ModelAdmin):
    list_display = ("vm", "event", "info", "logdt")
    list_filter = ["logdt"]
    

admin.site.register(VmRegistry, VmRegistryAdmin)
admin.site.register(VmTrail, VmTrailAdmin)