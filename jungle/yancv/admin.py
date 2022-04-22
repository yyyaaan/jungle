from django.contrib import admin

from .models import *

class CvCertAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CvCert._meta.get_fields()]
    list_filter = ["enabled"]

class CvExpAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CvExp._meta.get_fields()]
    list_filter = ["enabled"]


admin.site.register(CvCert, CvCertAdmin)
admin.site.register(CvExp, CvExpAdmin)