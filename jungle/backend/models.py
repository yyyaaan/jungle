from django.contrib import admin
from django.db import models
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class VmRegistry(models.Model):
    vmid = models.CharField("Assigned VMID", max_length=20, primary_key=True)
    
    project = models.CharField("Project", max_length=99)
    role = models.CharField("Usage Role", max_length=20)
    provider = models.CharField("Cloud providor", max_length=10)
    zone = models.CharField("Zone", max_length=20)
    resource = models.CharField("Resource Id", blank=True, max_length=99)
    batchnum = models.IntegerField("BatchN")


class VmTrail(models.Model):
    vm = models.ForeignKey(VmRegistry, on_delete=models.CASCADE,)

    event = models.CharField("Event description", max_length=1023)
    info = models.CharField("Information", max_length=9999)
    logdt = models.DateTimeField("Timestamp of Event")

    @admin.display(boolean=True, ordering="-logdt", description="Event within 24hrs")
    def is_within_24_hours(self):
        return self.logdt >= (timezone.now() - timedelta(days=1)) 

    def __str__(self):
        return f"{self.event} from {self.vmid} on {self.logdt}"
