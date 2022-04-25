from django.shortcuts import render
from django.core import serializers

from .models import *

def cv(request):
    certs = CvCert.objects.all().filter(enabled=True)
    # some processing are done in html
    return render(request, 'yancv/cv.html', {
        "h1text": "Under Construction",
        "certs": certs
    })

