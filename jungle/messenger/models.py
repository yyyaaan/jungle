from django.db import models
from django.db import models
from logging import getLogger

from commonlib.secretmanager import get_secret

logger = getLogger("messenger")

# Create your models here.
class MessengerData(models.Model):
    audience = models.CharField("Target Audience", max_length=99)
    provider = models.CharField("Service Provider", max_length=20, blank=True)
    text = models.CharField("Text", max_length=20)
    richcontent = models.TextField("Rich Content", max_length=65535, blank=True)
    response = models.TextField("Response", max_length=65535, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

