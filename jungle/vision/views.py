from django.shortcuts import render
from django import forms
from base64 import b64encode
from json import dumps

from .models import *

class VisionDBForm(forms.ModelForm):
    class Meta:
        model = VisionDB
        exclude = ('outjson',)


def hello(request):
    form = VisionDBForm(request.POST, request.FILES)

    if request.method != 'POST':
        return render(request, 'vision/index.html', {'form': form, "debug": "Start"})
    if not form.is_valid():
        form = VisionDBForm()
        return render(request, 'vision/index.html', {'form': form, "debug": "Error"})

    form.save()
    img_obj = form.instance

    # Doing AI
    if img_obj.aimodel == "AZ": 
        detector = AZDetector()
    elif img_obj.aimodel == "mn": 
        detector = BaseDetector()
    else:
        detector = YoloDetector(model_selection=str(img_obj.aimodel))
    img, analysis = detector.readImage(source=img_obj.userimage.path, display=False)

    # image is rendered using base64 (not saved)
    _, frame_buff = cv2.imencode('.jpg', img) 
    b64img = b64encode(frame_buff).decode("UTF-8")
    analysis = dumps(analysis, indent=4)


    return render(
        request, 'vision/index.html', 
        {'form': form, "debug": "Vision", "img_obj": img_obj, "imgbytes": b64img, "analysis": analysis})
