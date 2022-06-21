from django.contrib import admin
from .models import *

class MessengerDataAmdin(admin.ModelAdmin):
    list_display = ("audience", "provider", "text", "response", "timestamp")

admin.site.register(MessengerData, MessengerDataAmdin)