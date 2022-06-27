from django.db import models
from logging import getLogger

logger = getLogger("webreader")


class WebTasks(models.Model):
    task = models.IntegerField(primary_key = True)
    isactive = models.BooleanField("Active?", default=True)
    group = models.CharField("Task Group", max_length=100, blank=True)
    webaddress = models.CharField("Web URL", max_length=9999)
    keyfield = models.CharField("XPATH", max_length=9999)
    display = models.CharField("Display Text", max_length=100)
    note = models.CharField("Note", max_length=255, blank=True)


class WebReader(models.Model):
    task = models.ForeignKey(WebTasks, on_delete=models.CASCADE)
    response = models.TextField("Response", max_length=1024*1024)
    status = models.CharField("Status", max_length=1023)
    info = models.TextField("Extra Info", max_length=1024*1024, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    class Meta:
        get_latest_by = 'timestamp'


class MarkItDown(models.Model):
    md = models.TextField("markdown", max_length=1024*1024, blank=True)
    enabled = models.BooleanField("Show?")

    def __str__(self):
        rowone = self.md.split("\n")[0]
        return rowone if self.enabled else f"[Disabled]: {rowone}"
