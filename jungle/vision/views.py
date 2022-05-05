from django.shortcuts import render
from django import forms
from base64 import b64encode
from json import dumps

from .models import *

class VisionDBForm(forms.ModelForm):
    class Meta:
        model = VisionDB
        exclude = ('outjson','userdesc')


def hello(request):
    form = VisionDBForm(request.POST, request.FILES)

    if request.method != 'POST':
        return render(request, 'vision/index.html', {'form': form, "debug": "Start"})
    if not form.is_valid():
        form = VisionDBForm()
        return render(request, 'vision/index.html', {'form': form, "debug": "Error"})

    form.save()
    img_obj = form.instance

    print ("model", img_obj.aimodel)
    # Doing AI
    if img_obj.aimodel == "AZ": 
        detector = AZDetector()
    elif img_obj.aimodel == "GCP": 
        detector = GCPDetector()
    elif img_obj.aimodel == "mn": 
        detector = BaseDetector()
    elif img_obj.aimodel == "husky": 
        detector = HuskyInTwoSteps()
    else:
        detector = YoloDetector(model_selection=str(img_obj.aimodel))
        
    img, analysis = detector.readImage(source=img_obj.userimage.path, display=False)

    # image is rendered using base64 (not saved)
    _, frame_buff = cv2.imencode('.jpg', img) 
    b64img = b64encode(frame_buff).decode("UTF-8")
    if type(analysis) == dict:
        analysis = dumps(analysis, indent=4, default=str)


    # save the result to VisionDB
    dbrecord = VisionDB.objects.get(pk=img_obj.id)
    dbrecord.outjson = str(analysis)
    dbrecord.userdesc = "frontend action"
    dbrecord.save()

    return render(
        request, 'vision/index.html', 
        {'form': form, "debug": "Vision", "img_obj": img_obj, "imgbytes": b64img, "analysis": analysis})
