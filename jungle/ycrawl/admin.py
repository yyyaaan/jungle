from django.contrib import admin

from .models import *

# Register your models here.

class VmRegistryAdmin(admin.ModelAdmin):
    list_display = ("vmid", "provider","project", "batchnum")
    

class VmTrailAdmin(admin.ModelAdmin):
    list_display = ("vmid", "event", "timestamp", "info")
    list_filter = ["timestamp"]
    

class VmActionLogAdmin(admin.ModelAdmin):
    # many-to-many use the Model Function name
    list_display = ("event", "vmids_applied", "timestamp", "info")
    list_filter = ["event", "timestamp"]



admin.site.register(VmRegistry, VmRegistryAdmin)
admin.site.register(VmTrail, VmTrailAdmin)
admin.site.register(VmActionLog, VmActionLogAdmin)