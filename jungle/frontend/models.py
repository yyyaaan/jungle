from django.db import models
from logging import getLogger

logger = getLogger("frontend")

class SiteUrl(models.Model):
    rawurl = models.CharField("Raw URL", primary_key = True, max_length=1023)
    cleanurl = models.CharField("Display URL", max_length=1023)
    menu1 = models.IntegerField("MainNav Order")
    menu2 = models.IntegerField("SideNav Order")
    menu3 = models.IntegerField("ListNav Order")
    desc1 = models.CharField("Desc-main", max_length=200, blank=True)
    desc2 = models.CharField("Desc-side", max_length=200, blank=True)
    desc3 = models.CharField("Desc-override", max_length=200, blank=True)
    icon = models.CharField("Icon", max_length=200, blank=True)
    style = models.CharField("Styling", max_length=999, blank=True)
