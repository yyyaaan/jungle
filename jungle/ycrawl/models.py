from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from logging import getLogger
from json import loads

logger = getLogger("ycrawl")


class VmRegistry(models.Model):
    vmid = models.CharField("Assigned VMID", max_length=20, primary_key=True)
    project = models.CharField("Project", max_length=99)
    role = models.CharField("Usage Role", max_length=20)
    provider = models.CharField("Cloud providor", max_length=10)
    zone = models.CharField("Zone", max_length=20)
    resource = models.CharField("Resource Id", blank=True, max_length=99)
    batchnum = models.IntegerField("BatchN")


class VmTrail(models.Model):
    vmid = models.CharField("Assigned VMID", max_length=20)
    event = models.CharField("Event", max_length=1023)
    info = models.CharField("Information", blank=True, max_length=9999)
    timestamp = models.DateTimeField(auto_now=True)

    @admin.display(boolean=True, ordering="-timestamp", description="Event within 24hrs")
    def is_within_24_hours(self):
        return self.timestamp >= (timezone.now() - timedelta(days=1)) 

    def __str__(self):
        return f"{self.event} from {self.vm} on {self.timestamp}"


class VmActionLog(models.Model):
    vmids = models.ManyToManyField(VmRegistry)
    event = models.CharField("Event description", max_length=1023)
    info = models.CharField("Information", blank=True, max_length=9999)
    result = models.CharField("Action Output", blank=True, max_length=9999)
    timestamp = models.DateTimeField(auto_now=True)

    @admin.display(boolean=True, ordering="-timestamp", description="Event within 24hrs")
    def is_within_24_hours(self):
        return self.timestamp >= (timezone.now() - timedelta(days=1)) 

    def vmids_applied(self):
        return ", ".join([x.vmid for x in self.vmids.all()])


class YCrawlConfig(models.Model):
    """Simple Tabular Data, contains validated JSON fields"""
    name = models.CharField(max_length=1023, primary_key=True)
    value = models.TextField("Value (json as str)", max_length=65535, blank=True)

    @classmethod
    def get_json_by_name(cls, name):
        return loads(cls.objects.get(pk=name).value)

    def clean(self):
        """Reject ill-formed vlaue"""
        try:
            loads(self.value)
        except Exception as e:
            raise ValidationError({"value": f"Invalid JSON. {str(e)}"})
        return self

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)