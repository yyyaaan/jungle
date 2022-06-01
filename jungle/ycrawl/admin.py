from django.contrib import admin

from .models import *

class YCrawlConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "value")
    ordering = ["name"]


class VmRegistryAdmin(admin.ModelAdmin):
    list_display = ("vmid", "provider","project", "batchnum")
    

class VmTrailAdmin(admin.ModelAdmin):
    list_display = ("vmid", "event", "timestamp", "info")
    list_filter = ["timestamp"]
    

class VmActionLogAdmin(admin.ModelAdmin):
    # many-to-many use the Model Function name
    list_display = ("event", "result", "vmids_applied", "timestamp", "info")
    list_filter = ["event", "timestamp"]


class BatchJobListAdmin(admin.ModelAdmin):
    # many-to-many use the Model Function name
    list_display = ("jobid", "vmid", "completion", "note", "weburl")
    list_filter = ["completion", "note", "vmid"]


admin.site.register(VmRegistry, VmRegistryAdmin)
admin.site.register(VmTrail, VmTrailAdmin)
admin.site.register(VmActionLog, VmActionLogAdmin)
admin.site.register(YCrawlConfig, YCrawlConfigAdmin)
admin.site.register(BatchJobList, BatchJobListAdmin)