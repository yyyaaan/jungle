from django.contrib import admin
from .models import *

class AdminWebTasks(admin.ModelAdmin):
    list_display = ("task", "isactive","group", "webaddress", "keyfield", "display", "note")
    

class AdminWebReader(admin.ModelAdmin):
    list_display = ("task", "response", "status", "timestamp", "info")
    list_filter = ["timestamp", "status"]
    

admin.site.register(WebTasks, AdminWebTasks)
admin.site.register(WebReader, AdminWebReader)
admin.site.register(MarkItDown)
admin.site.register(MyDoc)