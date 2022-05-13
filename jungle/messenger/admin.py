from django.contrib import admin
from .models import *

class MessengerDataAmdin(admin.ModelAdmin):
    list_display = ("audience", "provider", "text", "richcontent", "response", "timestamp")

admin.site.register(MessengerData, MessengerDataAmdin)