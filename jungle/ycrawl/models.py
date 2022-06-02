from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta
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
        return f"{self.event} from {self.vmid} on {self.timestamp}"


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
    value = models.TextField("Value (str / json as str)", max_length=65535, blank=True)

    @classmethod
    def get_json_by_name(cls, name):
        return loads(cls.objects.get(pk=name).value)

    @classmethod
    def get_value(cls, name):
        return cls.objects.get(pk=name).value

    def clean(self):
        """Reject ill-formed json"""
        if ":" in self.value and "{" in self.value:
            try:
                loads(self.value)
            except Exception as e:
                raise ValidationError({"value": f"Invalid JSON. {str(e)}"})
        return self

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    
class BatchJobList(models.Model):
    """Job List with Assigned VMID"""
    jobid = models.CharField(max_length=100, primary_key=True)
    vmid = models.ForeignKey(VmRegistry, on_delete=models.CASCADE)
    weburl = models.CharField(max_length=65535)
    completion = models.BooleanField("Completed?", default=False)
    note = models.CharField(max_length=1023, blank=True)

    @property
    def nodejob(self):
        return f'node node_handler.js {self.jobid} "{self.weburl}"'

    @classmethod
    def get_today_objects(cls):
        return cls.objects.filter(jobid__startswith=date.today().strftime("%Y%m%d"))




