from django.shortcuts import render
from django.core import serializers

from .models import *

def cv(request):

    # certs = serializers.serialize("json", )
    certs = CvCert.objects.all().filter(enabled=True)
    print (certs)
    return render(request, 'yancv/cv.html', {
        "h1text": "Under Construction",
        "certs": certs
    })

